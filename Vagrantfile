DEFAULT_BASE_BOX = "bento/ubuntu-16.04"
Vagrant.configure("2") do |config|
  ui = Vagrant::UI::Colored.new
    machines = {    
	:Hadoop => {:ip => '192.168.56.11', :mem => '1024', :cpu => 2},
  :ClickHouse => {:ip => '192.168.56.12', :mem => '1024', :cpu => 1},
  }
  config.vm.box = DEFAULT_BASE_BOX

  machines.each do |machine_name, machine_details|
    config.vm.define machine_name do |machine_config|
      machine_ip = machine_details[:ip]
      ui.info("Handling vm with hostname [#{machine_name.to_s}] and IP [#{machine_ip}]")
      machine_config.vm.box = machine_details[:box] ||= DEFAULT_BASE_BOX
      machine_config.vm.network :private_network, ip: machine_ip
      machine_config.vm.hostname = machine_name.to_s
      machine_config.vm.provider :virtualbox do |vb|
        reserved_mem = machine_details[:mem] || default_mem
        reserved_cpu = machine_details[:cpu] || default_cpu
        vb.name = machine_name.to_s
        vb.customize ["modifyvm", :id, "--groups", "/EG_home_work"]
        vb.customize ["modifyvm", :id, "--memory", reserved_mem]
        vb.customize ["modifyvm", :id, "--cpus", reserved_cpu]
        vb.gui = false
      end #vb
    end #machine_config
  end #machines

  config.vm.define 'eg' do |machine|
    machine.vm.synced_folder "./", "/vagrant", owner: "vagrant", mount_options: ["dmode=775,fmode=775"]
    machine.vm.network "private_network", ip: "192.168.56.105"
  machine.vm.provider :virtualbox do |vb|
      vb.name = "EG_Home"
      vb.customize ["modifyvm", :id, "--groups", "/EG_home_work"]
      vb.customize ["modifyvm", :id, "--memory", 2048]
      vb.customize ["modifyvm", :id, "--cpus", 1]
      vb.gui = false
  end
  machine.vm.provision :shell do |s|
	  s.inline = "sudo apt -y update && sudo apt install -y python-minimal \
	    && sudo apt install python-pip -y \
	    && sudo apt -y install screen vim git \
		  && sudo pip install --upgrade pip \
	    && sudo pip install virtualenv \
	    && sudo pip install ansible==2.4.2.0 \
      && cd /vagrant/"
  end
  machine.vm.hostname = 'eg.local'
#  machine.vm.provision "ansible" do |ansible|
#    ansible.playbook = "main.yml"
#  end
  end
end