import random

from helga.plugins import match


descriptors = ('Abstract', 'Base', 'Lazy', 'Mutable', 'Composite', 'Recursive',
               'Asynchronous', 'Shared', 'Runnable', 'Secure', 'Generic', 'Internal',
               'External', 'Prioritized',
               )

frameworks = ('Swing', 'Hibernate', 'JDBC', 'Spring', 'Struts', 'Android', 'AWT',
              '', '', '', ''  # Additional weight for random choice
              )

things = ('Printer', 'Internet', 'Synergy', 'IRC', 'Window', 'Network', 'TCP', 'Protocol',
          'Data', 'Web', 'Script', 'Command', 'Television', 'UML', 'Null', 'Scheduler',
          'Bandwidth', 'Bot', 'Computation', 'Event', 'Color', 'Font', 'Logger', 'Hash',
          'SOAP', 'XML', 'JSON', 'HTTP', 'REST', 'Layout', 'Cache', 'List', 'Enum', 'Device',
          'Statement', 'Memory', 'Timestamp', 'Graph', 'Result', 'Grid', 'Category', 'Story',
          'Article', 'Model', 'Tokenizer',
          )

actions = ('Extraction', 'Mutation', 'Automation', 'Interpolation', 'Instantiation',
           'Translation', 'Iteration', '', '', '', '',  # Additional weight for random choice
           )

oop = ('Thread', 'Bean', 'Command', 'Prototype', 'Factory', 'Builder', 'Singleton', 'Client',
       'Exception', 'Error', 'Pool', 'Decorator', 'Controller', 'Proxy', 'Module', 'Adapter',
       'Bridge', 'Wrapper', 'Iterator', 'Observer', 'Interpreter', 'Applet', 'Action', 'Map',
       'Queue', 'Configuration', 'Encoder', 'Tokenizer',
       )


@match(r'(lol)?java(?!script)', priority=0)
def make_bullshit_java_thing(client, channel, nick, message, matches):
    """
    Java class naming is hilariously enterprise...
    """
    return (random.choice(descriptors) +
            random.choice(frameworks) +
            random.choice(things + oop) +
            random.choice(actions) +
            random.choice(oop))
