import datetime

from itertools import ifilter, imap

import pytz
import smokesignal

from twisted.internet import reactor

from helga import log, settings
from helga.db import db
from helga.plugins import command, random_ack


logger = log.getLogger(__name__)


in_seconds_map = {
    'm': 60,
    'h': 3600,
    'd': 86400,
}

# This is how python datetime does it
days_of_week = {
    'M':  0,
    'Tu': 1,
    'W':  2,
    'Th': 3,
    'F':  4,
    'Sa': 5,
    'Su': 6,
}
days_of_week_lookup = dict((v, k) for k, v in days_of_week.iteritems())

_scheduled = set()


@smokesignal.on('signon')
def init_reminders(client):
    global _scheduled

    now = datetime.datetime.utcnow()
    logger.info("Initializing any scheduled reminders")

    for reminder in db.reminders.find():
        # Update the record to ensure a hash
        if 'hash' not in reminder or reminder['hash'] != str(reminder['_id'])[:6]:
            db.reminders.update({'_id': reminder['_id']}, {'$set': {'hash': str(reminder['_id'])[:6]}})

        if reminder['_id'] in _scheduled:
            continue

        if reminder['when'].tzinfo is not None:
            now = now.replace(tzinfo=pytz.UTC).astimezone(reminder['when'].tzinfo)

        diff = reminder['when'] - now
        delay = (diff.days * 24 * 3600) + diff.seconds

        if delay < 0:
            logger.warning("Event has already happened :(")
            if 'repeat' in reminder:
                reminder['when'], _ = next_occurrence(reminder)
                db.reminders.save(reminder)

                diff = reminder['when'] - now
                delay = (diff.days * 24 * 3600) + diff.seconds
                logger.info("Reminder delayed until next occurrence: {0} seconds from now".format(delay))
            elif delay >= -60:  # if it's only 1 minute late
                logger.info("Reminder is only a little late. Go now!")
                delay = 0
            else:
                logger.info("Removing stale, non-repeating reminder")
                db.reminders.remove(reminder['_id'])
                continue

        _scheduled.add(reminder['_id'])
        reactor.callLater(delay, _do_reminder, reminder['_id'], client)


def readable_time_delta(seconds):
    """
    Convert a number of seconds into readable days, hours, and minutes
    """
    days = seconds // 86400
    seconds -= days * 86400
    hours = seconds // 3600
    seconds -= hours * 3600
    minutes = seconds // 60

    m_suffix = 's' if minutes != 1 else ''
    h_suffix = 's' if hours != 1 else ''
    d_suffix = 's' if days != 1 else ''

    retval = '{0} minute{1}'.format(minutes, m_suffix)

    if hours != 0:
        retval = '{0} hour{1} and {2}'.format(hours, h_suffix, retval)

    if days != 0:
        retval = '{0} day{1}, {2}'.format(days, d_suffix, retval)

    return retval


def next_occurrence(reminder):
    """
    Calculate the next occurrence of a repeatable reminder
    """
    now = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)
    now_dow = now.weekday()

    # Modded range from tomorrow until 1 week from now
    dow_iter = imap(lambda x: x % 7, xrange(now_dow + 1, now_dow + 8))

    # Filter out any days that aren't in the schedule
    dow_iter = ifilter(lambda x: x in reminder['repeat'], dow_iter)

    # Get the first one. That's the next day of week
    try:
        next_dow = next(dow_iter)
    except StopIteration:  # How?
        logger.exception("Somehow, we didn't get a next day of week?")
        _scheduled.discard(reminder['_id'])
        return

    # Get the real day delta
    day_delta = (next_dow if next_dow > now_dow else next_dow + 7) - now_dow

    # Update the record
    return reminder['when'] + datetime.timedelta(days=day_delta), day_delta


def _do_reminder(reminder_id, client):
    global _scheduled

    reminder = db.reminders.find_one(reminder_id)
    if not reminder:
        logger.error("Tried to locate reminder {0}, but it returned None".format(reminder_id))
        _scheduled.discard(reminder_id)

    client.msg(str(reminder['channel']), str(reminder['message']))

    # If this repeats, figure out the next time
    if 'repeat' in reminder:
        # Update the record
        reminder['when'], day_delta = next_occurrence(reminder)
        db.reminders.save(reminder)

        _scheduled.add(reminder_id)
        reactor.callLater(day_delta * 86400, _do_reminder, reminder_id, client)
    else:
        _scheduled.discard(reminder_id)
        db.reminders.remove(reminder_id)


def in_reminder(client, channel, nick, args):
    """
    Create a one-time reminder to occur at some amount of minutes, hours, or days
    in the future. This is used like:

        <sduncan> helga in 12h submit timesheet

    This will create a reminder 12 hours from now with the message "submit timesheet".

    Optionally, a specific channel can be specified to receive the reminder message. This
    is useful if creating several reminders via a private message. To use this, specify
    "on <channel>" between the time amount and the message:

        <sduncan> helga in 12h on #bots submit timesheet
        <sduncan> helga in 12h on bots submit timesheet

    Note that the '#' char for specifying the channel is entirely optional.
    """
    global _scheduled

    amount, quantity = int(args[0][:-1]), args[0][-1]

    # Handle ability to specify the channel
    if args[1] == 'on':
        target_channel = args[2]
        message = ' '.join(args[3:])

        # Make sure channel is formatted correctly
        if not target_channel.startswith('#'):
            target_channel = '#{0}'.format(target_channel)
    else:
        target_channel = channel
        message = ' '.join(args[1:])

    if quantity not in in_seconds_map:
        return "Sorry I didn't understand '{0}'. You must specify m,h,d. Ex: 12m".format(args[0])

    seconds = amount * in_seconds_map[quantity]
    utcnow = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)
    delta = datetime.timedelta(seconds=seconds)

    id = db.reminders.insert({
        'when': utcnow + delta,
        'message': message,
        'channel': target_channel,
        'creator': nick,
    })

    # Update the record to ensure a hash
    db.reminders.update({'_id': id}, {'$set': {'hash': str(id)[:6]}})

    _scheduled.add(id)
    reactor.callLater(seconds, _do_reminder, id, client)
    return 'Reminder set for {0} from now'.format(readable_time_delta(seconds))


def at_reminder(client, channel, nick, args):
    """
    Schedule a reminder to occur at a specific time. The given time can optionally
    be specified to occur at a specific timezone, but will default to the value
    of settings.TIMEZONE if none is specified. Times should be on a 24-hour clock.

    These types of reminders are repeatable, should the last two words of the message
    be of the form "repeat <days_of_week>" where days_of_week is a single string consisting
    of any of the following days: M, Tu, W, Th, F, Sa, Su. For example, 'repeat MWF'
    will repeat a reminder at the same time every Monday, Wednesday, and Friday.

    A full example of how one would use this:

        <sduncan> helga at 13:00 EST standup time repeat MTuWThF

    This will create a reminder "standup time" to occur at 1:00PM Eastern every weekday.

    Optionally, a specific channel can be specified to receive the reminder message. This
    is useful if creating several reminders via a private message. To use this, specify
    "on <channel>" between the time amount and the message:

        <sduncan> helga at 13:00 EST on #bots standup time repeat MTuWThF
        <sduncan> helga at 13:00 EST on bots standup time repeat MTuWThF

    Note that the '#' char for specifying the channel is entirely optional.
    """
    global _scheduled

    now = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)

    # Parse the time it should go off, and the minute offset of the day
    hh, mm = map(int, args[0].split(':'))
    next = now.replace(hour=hh, minute=mm)

    # Strip time from args
    args = args[1:]

    # Default timezone
    timezone = pytz.timezone(settings.TIMEZONE)

    try:
        # If there was a timezone passed in
        timezone = pytz.timezone(args[0])
    except pytz.UnknownTimeZoneError:
        pass
    else:
        # If so, remove it from args
        args = args[1:]

    # Now is already UTC current, so just adjust. Next is set without a timezone
    local_now = now.astimezone(timezone)
    local_next = next.replace(tzinfo=timezone)

    if local_next <= local_now:
        local_next += datetime.timedelta(days=1)

    reminder = {
        'when': local_next.astimezone(pytz.UTC),
        'channel': channel,
        'message': ' '.join(args),
        'creator': nick,
    }

    # Check for 'repeat' arg
    try:
        repeat = args[-2] == 'repeat'
    except IndexError:
        repeat = False

    if repeat:
        # If repeating, strip off the last two for the message
        sched = args[-1]
        reminder['message'] = ' '.join(args[:-2])
        repeat_days = sorted([v for k, v in days_of_week.iteritems() if k in sched])

        if not repeat_days:
            return "I didn't understand '{0}'. You must use any of M,Tu,W,Th,F,Sa,Su. Ex: MWF".format(sched)

        reminder['repeat'] = repeat_days

        for attempt in xrange(7):
            if reminder['when'].weekday() in repeat_days:
                break
            reminder['when'] += datetime.timedelta(days=1)

    # Handle ability to specify the channel
    if reminder['message'].startswith('on'):
        parts = reminder['message'].split(' ')
        chan = parts[1]
        reminder['message'] = ' '.join(parts[2:])

        # Make sure channel is formatted correctly
        if not chan.startswith('#'):
            chan = '#{0}'.format(chan)
        reminder['channel'] = chan

    id = db.reminders.insert(reminder)

    # Update the record to ensure a hash
    db.reminders.update({'_id': id}, {'$set': {'hash': str(id)[:6]}})

    diff = reminder['when'] - now
    delay = (diff.days * 24 * 3600) + diff.seconds

    _scheduled.add(id)
    reactor.callLater(delay, _do_reminder, id, client)
    return 'Reminder set for {0} from now'.format(readable_time_delta(delay))


def list_reminders(client, nick, channel):
    reminders = []

    for reminder in db.reminders.find({'channel': channel}):
        about = "[{0}] At {1}: '{2}'"

        hash = str(reminder['_id'])[:6]
        when = reminder['when'].strftime('%m/%d/%y %H:%M UTC')

        about = about.format(hash, when, reminder['message'])

        if 'repeat' in reminder:
            days = [days_of_week_lookup[value] for value in reminder['repeat']]
            about = '{0} (Repeat every {1})'.format(about, ','.join(days))

        reminders.append(about)

    if not reminders:
        client.msg(nick, 'There are no reminders for channel: {0}'.format(channel))
    else:
        reminders.insert(0,  '{0}, here are the reminders for channel: {1}'.format(nick, channel))
        client.msg(nick, '\n'.join(reminders))


def delete_reminder(channel, hash):
    rec = db.reminders.find_one({'hash': hash})

    if rec is not None:
        db.reminders.remove(rec['_id'])
        return random_ack()
    else:
        return "No reminder found with hash '{0}'".format(hash)


@command('reminders', aliases=['in', 'at'],
         help="Schedule reminders. Usage: helga ("
              "in ##(m|h|d) [on <channel>] <message>|"
              "at <HH>:<MM> [<timezone>] [on <channel>] <message> [repeat <days_of_week]|"
              "list [channel]|"
              "delete <hash>). "
              "Ex: 'helga in 12h take out the trash' or 'helga at 13:00 EST standup time repeat MTuWThF'")
def reminders(client, channel, nick, message, cmd, args):
    if cmd == 'in':
        return in_reminder(client, channel, nick, args)
    elif cmd == 'at':
        return at_reminder(client, channel, nick, args)
    elif cmd == 'reminders':
        if args[0] == 'list':
            client.me(channel, 'whispers to {0}'.format(nick))
            list_reminders(client, nick, (args[1] if len(args) >= 2 else channel))
            return None
        elif args[0] == 'delete':
            return delete_reminder(channel, args[1])
