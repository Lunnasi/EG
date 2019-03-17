DEFAULT_BASE_BOX = "bento/ubuntu-16.04"
Vagrant.configure("2") do |config|
  ui = Vagrant::UI::Colored.new
    machines = {    
#	:master => {:ip => '192.168.56.11', :mem => '2048', :cpu => 1},
#  :node1 => {:ip => '192.168.56.12', :mem => '2048', :cpu => 1},
#  :node2 => {:ip => '192.168.56.13', :mem => '2048', :cpu => 1},
  :clickhouse => {:ip => '192.168.56.14', :mem => '1024', :cpu => 1},
  :EGHome => {:ip => '192.168.56.105', :mem => '1024', :cpu => 1},
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

#  machine.vm.provision "ansible" do |ansible|
#    ansible.playbook = "main.yml"
#  end
end