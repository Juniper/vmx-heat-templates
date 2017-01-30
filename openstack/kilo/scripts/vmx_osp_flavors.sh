#Copyright (c) Juniper Networks, Inc., 2017-2024.
#All rights reserved.

reflv=$1
remem=4096
rehdd=40
revcpu=1

pfeflv=$2
pfemem=12288
pfehdd=40
pfevcpu=7

compute1=$3
compute2=$4
hugepage_sz=2048

aname="global-group"
attr="global-grouppinned"

nova flavor-create --is-public true $reflv auto $remem $rehdd $revcpu
nova flavor-key $reflv set aggregate_instance_extra_specs:$attr=true
nova flavor-key $reflv set hw:cpu_policy=dedicated
nova aggregate-create $aname
nova aggregate-set-metadata $aname $attr=true
nova aggregate-add-host $aname $compute1
nova aggregate-add-host $aname $compute2
nova flavor-create --is-public true $pfeflv auto $pfemem $pfehdd $pfevcpu
nova flavor-key $pfeflv set aggregate_instance_extra_specs:$attr=true
nova flavor-key $pfeflv set hw:cpu_policy=dedicated
#nova flavor-key $pfeflv set hw:mem_page_size=$hugepage_sz
