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

  config.vm.provision "shell", inline: "sudo apt-get update -qq"
  config.vm.provision "shell", inline: "sudo apt-get install -qqy --force-yes mongodb ngircd"
end
