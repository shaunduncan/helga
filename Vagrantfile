# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "precise64"
  config.vm.box_url = "http://files.vagrantup.com/precise64.box"

  # Forward keys from SSH agent rather than copypasta
  config.ssh.forward_agent = true

  # FIXME: Might not even need this much
  config.vm.provider "virtualbox" do |v|
      v.customize ["modifyvm", :id, "--memory", "1024"]
  end

  # Forward ports for irc(6667) and mongo(27017)
  config.vm.network :forwarded_port, guest: 6667, host: 6667
  config.vm.network :forwarded_port, guest: 27017, host: 27017
  config.vm.network :private_network, ip: "192.168.10.101"

  config.vm.provision "shell", inline: <<EOF
# Update and install system dependencies
apt-get update -qq
apt-get install -qqy --force-yes \
  git \
  mongodb \
  ngircd \
  openssl \
  libssl-dev \
  python-dev \
  python-pip \
  python-setuptools \
  python-virtualenv \
  libffi6 \
  libffi-dev

# Allow external mongo connections
sed -i -s 's/^bind_ip = 127.0.0.1/#bind_ip = 127.0.0.1/' /etc/mongodb.conf
service mongodb restart

# Create a virtualenv for helga and install
sudo -u vagrant virtualenv /home/vagrant/helga_venv
pushd /vagrant
# upgrade pip from the archaic 1.1
sudo -u vagrant /home/vagrant/helga_venv/bin/pip install --upgrade pip
# install helga
sudo -u vagrant /home/vagrant/helga_venv/bin/python setup.py develop
popd

# Make sure the default profile activates the venv
sudo -u vagrant echo "#!/bin/bash" > /home/vagrant/.profile
sudo -u vagrant echo "source /home/vagrant/helga_venv/bin/activate" >> /home/vagrant/.profile
sudo -u vagrant echo "cd /vagrant/" >> /home/vagrant/.profile

EOF
end
