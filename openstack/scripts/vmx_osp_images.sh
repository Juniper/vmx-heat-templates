#Copyright (c) Juniper Networks, Inc., 2017-2024.
#All rights reserved.

re_img_name=$1
re_img=$2
pfe_img_name=$3
pfe_img=$4

glance image-create --name $re_img_name --file $re_img --disk-format qcow2 --container-format bare --property hw_cdrom_bus=ide --property hw_disk_bus=ide --property hw_vif_model=virtio
glance image-create --name $pfe_img_name --file $pfe_img --disk-format vmdk --container-format bare --property hw_cdrom_bus=ide --property hw_disk_bus=ide --property hw_vif_model=virtio
