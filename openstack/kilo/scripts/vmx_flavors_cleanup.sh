#Copyright (c) Juniper Networks, Inc., 2017-2024.
#All rights reserved.

reflv=$1
pfeflv=$2
compute1=$3
compute2=$4

aname="global-group"

nova flavor-delete $reflv
nova flavor-delete $pfeflv

nova aggregate-remove-host $aname $compute1
nova aggregate-remove-host $aname $compute2
nova aggregate-delete $aname

