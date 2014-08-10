#!/bin/bash

# Copyright (c) 2014, Ondrej Balaz. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# * Neither the name of the original author nor the names of contributors
#   may be used to endorse or promote products derived from this software
#   without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# NOTES:
# To re-pack root/boot archives use: $ tar -jcvf root.tar.bz2 -C p2 .

# Constants
DRY_RUN=
PRINT_CONF=
USE_DEVEL=
IMG=
MOUNT_ROOT=/tmp
NO_UMOUNT=

# Commands
FDISK=/sbin/fdisk                   # util-linux fdisk NOT GNU!
KPARTX=/sbin/kpartx
LOSETUP=/sbin/losetup
DD=/bin/dd
MOUNT=/bin/mount
UMOUNT=/bin/umount
MKFSVFAT=/sbin/mkfs.vfat
MKFSEXT4=/sbin/mkfs.ext4
TAR=/bin/tar
SYNC=/bin/sync
LN=/bin/ln
CP=/bin/cp


#
# Functions
#
# Print short help message
help() {
	cat <<EOF
$(basename $0) - build SD card image for vjezd application
Usage $(basename $0) [options] /path/to/image

Available options:
-c, --config            just print configuration, not generate image
-d, --dry-run           don't do anything, print commands
-h, --help              show this help message and exit
-D, --devel             use development versions (in script directory)
-u, --no-umount         don't umount prepared image (you MUST do it yourself)

Available image configuration options:
--run-vjezd             run vjezd service in image*
--run-tcpgpio           run tcpgpio service in image*
--run-mysql             run MySQL service in image

--id=ID                 device identifier (1 to 8 [a-zA-Z0-9] characters)
--mode=MODE             device mode (print,scan,both,auto) (default: auto)
--port-button=PORT      button port (default gpio:22)
--port-printer=PORT     printer port (default cups:72)
--port-relay=PORT       relay port (default tcpgpio:192.168.1.4,7777,11)
--port-scanner=PORT     scanner port (default evdev:/dev/input/scanner)
--db-host=HOST          database host (default: 192.168.1.1)
--db-dbname=DBNAME      database name (default: vjezd)
--db-user=USER          database user (default: vjezd)
--db-password=PASSWORD  database password (default: vjezd123)

--ip=IP                 image ip address (if ommited will use DHCP)
--netmask=NETMASK       image ip netmask (default: 255.255.255.0)
--gateway=IP            image ip gateway address
--nameserver=           image ip nameserver (whitespace separated)

Notes:
* To delete option (e.g. port) use --port-button=
* As both --run-vjezd and --run-tcpgpio use GPIO please ensure that in image
which is configured by both vjezd uses tcpgpio and not gpio button/relay
directly.
EOF
}

# Yield error and exit
error() {
	echo error: $1 1>&2

	echo
	echo !!! WARNING !!!
	echo Script ended unexpectedly. Consult mount command and mapper settings
	echo and recover using commands below before re-runing the script.
	echo
	echo \# $LOSETUP -d /dev/loopX
	echo \# $UMOUNT /dev/mapper/loopXp1
	echo \# $UMOUNT /dev/mapper/loopXp2
	echo \# $KPARTX -d /path/to/image
	echo

	exit $2
}


#
# Pre-flight checks
#
# Check if run as root
if [[ $EUID -ne 0 ]]; then
	error "You must be root to do this" 1
fi

# Check if all required tools are available
missing=
[ -x $FDISK ] || missing="fdisk $(missing)"
[ -x $KPARTX ] || missing="kpartx $(missing)"
[ -x $LOSETUP ] || missing="losetup $(missing)"
[ -x $DD ] || missing="dd $(missing)"
[ -x $MOUNT ] || missing="mount $(missing)"
[ -x $UMOUNT ] || missing="umount $(missing)"
[ -x $MKFSVFAT ] || missing="mkfs.vfat $(missing)"
[ -x $MKFSEXT4 ] || missing="mkfs.ext4 $(missing)"
[ -x $TAR ] || missing="tar $(missing)"
[ -x $SYNC ] || missing="sync $(missing)"
[ -x $LN ] || missing="ln $(missing)"
[ -x $CP ] || missing="cp $(missing)"

# Exit when requirements arent met
[ -z "$missing" ] || error "Following requirements are missing: $missing" 1


#
# Main
#
# Configure the image
conf_run_vjezd=
conf_run_tcpgpio=
conf_run_mysql=
conf_id=
conf_mode=auto
conf_port_button=gpio:22
conf_port_printer=cups:72
conf_port_relay=tcpgpio:192.168.1.4,7777,11
conf_port_scanner=evdev:/dev/input/scanner
conf_db_host=192.168.1.1
conf_db_dbname=vjezd
conf_db_user=vjezd
conf_db_password=vjezd
conf_ip=
conf_netmask=255.255.255.0
conf_gateway=
conf_nameserver=

ARGS=$(getopt -o "hdcDU" \
	-l "run-vjezd,run-tcpgpio,run-mysql" \
	-l "id:,mode:,port-button:,port-printer:,port-relay:,port-scanner:" \
	-l "db-host:,db-dbname:,db-user:,db-password:" \
	-l "ip:,netmask:,gateway:,nameserver:" \
	-l "config,dry-run,help,devel,no-umount" \
	-n "error" \
	-- $@)
[ $? -ne 0 ] && exit 1

eval set -- "$ARGS"
while true; do
	case $1 in
		--run-vjezd)
			conf_run_vjezd=1
			shift ;;
		--run-tcpgpio)
			conf_run_tcpgpio=1
			shift ;;
		--run-mysql)
			conf_run_mysql=1
			shift ;;
		--id)
			conf_id=$2
			shift 2 ;;
		--mode)
			conf_mode=$2
			shift 2 ;;
		--port-button)
			conf_port_button=$2
			shift 2 ;;
		--port-printer)
			conf_port_printer=$2
			shift 2 ;;
		--port-relay)
			conf_port_relay=$2
			shift 2 ;;
		--port-scanner)
			conf_port_scanner=$2
			shift 2 ;;
		--db-host)
			conf_db_host=$2
			shift 2 ;;
		--db-dbname)
			conf_db_dbname=$2
			shift 2 ;;
		--db-user)
			conf_db_user=$2
			shift 2 ;;
		--db-password)
			conf_db_password=$2
			shift 2 ;;
		--ip)
			conf_ip=$2
			shift 2 ;;
		--netmask)
			conf_netmask=$2
			shift 2 ;;
		--gateway)
			conf_gateway=$2
			shift 2 ;;
		--nameserver)
			conf_nameserver=$2
			shift 2 ;;

		-h|--help)
			help
			exit 0 ;;
		-c|--config)
			PRINT_CONF=1
			shift ;;
		-d|--dry-run)
			DRY_RUN=echo
			shift ;;
		-D|--devel)
			USE_DEVEL=1
			shift ;;
		-U|--no-umount)
			NO_UMOUNT=1
			shift ;;

		--)
			shift
			break ;;
	esac
done

# Image output path is non-option
[ $# -lt 1 ] && error "image output path expected" 1
IMG=$1

# Option checks and post-processing
# Disallow empty image
[ -z "$conf_run_vjezd" -a -z "$conf_run_tcpgpio" -a -z "$conf_run_mysql" ] \
	&& error "at least one of vjezd, tcpgpio or mysql services must be run!" 1

# Id must be set
[ ! -z "$conf_run_vjezd" ] && [ -z "$conf_id" ] \
	&& error "device unique id must be set" 1

# Ports
[ ! -z "$conf_port_button" ] && conf_port_button="button=$conf_port_button"
[ ! -z "$conf_port_printer" ] && conf_port_printer="printer=$conf_port_printer"
[ ! -z "$conf_port_relay" ] && conf_port_relay="relay=$conf_port_relay"
[ ! -z "$conf_port_scanner" ] && conf_port_scanner="scanner=$conf_port_scanner"


# Generate configuration file
read -d '' CONF_FILE << EOF
[device]
id=$conf_id
mode=$conf_mode

[ports]
$conf_port_button
$conf_port_printer
$conf_port_relay
$conf_port_scanner

[log]
level=WARNING
dest=console,/var/log/vjezd.log
append=false

[db]
host=$conf_db_host
dbname=$conf_db_dbname
user=$conf_db_user
password=$conf_db_password
EOF

# Generate /etc/interfaces file
if ! [ -z $conf_ip ]; then
	# Static address
	[ ! -z "$conf_ip" ] && conf_ip="address $conf_ip"
	[ ! -z "$conf_netmask" ] && conf_netmask="netmask $conf_netmask"
	[ ! -z "$conf_gateway" ] && conf_gateway="gateway $conf_gateway"

	read -d '' IFACES_FILE << EOF
auto lo

iface lo inet loopback
iface eth0 inet static
$conf_ip
$conf_netmask
$conf_gateway

allow-hotplug wlan0
iface wlan0 inet manual
wpa-roam /etc/wpa_supplicant/wpa_supplicant.conf
iface default inet dhcp
EOF
else
	read -d '' IFACES_FILE << EOF
auto lo

iface lo inet loopback
iface eth0 inet dhcp

allow-hotplug wlan0
iface wlan0 inet manual
wpa-roam /etc/wpa_supplicant/wpa_supplicant.conf
iface default inet dhcp
EOF
fi

# Generate /etc/resolv.conf file
RESOLV_FILE=
if [ ! -z "$conf_nameserver" ]; then
	for i in $conf_nameserver ; do
		RESOLV_FILE="$RESOLV_FILEnameserver $i"
	done
fi

echo
echo !!! WARNING !!!
echo This script auto-generates configuration files but not validates them.
echo Applications may crash if configuration is invalid.
echo

if ! [ -z "$conf_run_vjezd" ]; then
	echo --- /opt/vjezd/vjezd.conf: ---
	echo "$CONF_FILE"
	echo
fi

echo --- /etc/network/interfaces: ---
echo "$IFACES_FILE"
echo

if ! [ -z "$RESOLV_FILE" ]; then
	echo --- /etc/resolv.conf ---
	echo "$RESOLV_FILE"
fi

# Exit if just printing config
[ ! -z "$PRINT_CONF" ] && exit

echo "Press ^C to abort in 5s"
sleep 5

# Generate image

# Prepare an empty image
echo
echo Preparing image in: ${IMG}...
echo
echo Creating image file...
$DRY_RUN $DD if=/dev/zero of=$IMG bs=1M count=2000
[ $? -ne 0 ] && exit "cannot create image file. Exiting" 2

# Partition image using fdisk
echo Partitioning image file...
imgdev=/dev/dryrun
if [ -z "$DRY_RUN" ]; then
	imgdev=$($LOSETUP -f --show $IMG)
	[ $? -ne 0 ] && exit "cannot create loop device. Exiting" 2
fi
$DRY_RUN $FDISK $imgdev << EOF
n
p
1

+64M
t
c
n
p
2


w
EOF
# fdisk will always fail for some reason. Just continue. If partitioning wasn't
# successfull kpartx won't do anyway.
#[ $? -ne 0 ] && error "cannot partition loop device. Exiting" 2

# Remove loopback device
$DRY_RUN $LOSETUP -d $imgdev

# Prepare partitions
echo Preparing image partitions
if [ -z "$DRY_RUN" ]; then
	imgdev=$($KPARTX -vas $IMG | sed -E 's/.*(loop[0-9])p.*/\1/g' | head -1)
	[ $? -ne 0 ] && error "cannot create mapper for ${imgdev}. Exiting" 2
	imgdev=/dev/mapper/$imgdev
else
	imgdev=/dev/mapper/dryrun
fi

echo Formatting image partitions...
$DRY_RUN $MKFSVFAT ${imgdev}p1
[ $? -ne 0 ] && error "cannot format ${imgdev}p1. Exiting" 2
$DRY_RUN $MKFSEXT4 ${imgdev}p2
[ $? -ne 0 ] && error "cannot format ${imgdev}p2. Exiting" 2

# Mount partitions to $MOUNT_ROOT/$IMG/{p1,p2}
echo Mounting image partitions...
mntdir=$MOUNT_ROOT/$(basename "$IMG")
$DRY_RUN mkdir -p $mntdir/{p1,p2}
[ $? -ne 0 ] && error "cannot create mount directory. Exiting" 2

for p in p1 p2 ; do
	$DRY_RUN $MOUNT ${imgdev}${p} $mntdir/${p}
	[ $? -ne 0 ] && error "cannot mount ${imgdev}${p}. Exiting" 2
done

# Untar files to image
echo Extracting boot and root files into image...
$DRY_RUN $TAR -jxvf image/boot.tar.bz2 -C $mntdir/p1
[ $? -ne 0 ] && error "unable to extract image/boot.tar.bz2. Exiting" 2
$DRY_RUN $TAR -jxvf image/root.tar.bz2 -C $mntdir/p2
[ $? -ne 0 ] && error "unable to extract image/root.tar.bz2. Exiting" 2

# First if its development version copy over all needed files
if [ ! -z "$USE_DEVEL" ]; then
	echo Copying development version files...
	$DRY_RUN $CP -r vjezd/ tcpgpio.{py,service} vjezd.{conf,py,service} \
		$mntdir/p2/opt/vjezd
	[ $? -ne 0 ] && error "cannot copy development files. Exiting" 2
fi

# Apply configuration (e.g. which services should run)
echo Configuring image...

echo Configuring services...
# vjezd
$DRY_RUN rm $mntdir/p2/etc/systemd/system/vjezd.service \
	$mntdir/p2/etc/systemd/system/multi-user.target.wants/vjezd.service
if [ ! -z "$conf_run_vjezd" ]; then
	$DRY_RUN $LN -s /opt/vjezd/vjezd.service $mntdir/p2/etc/systemd/system
	[ $? -ne 0 ] && error "cannot link vjezd.service. Exiting" 2
	$DRY_RUN $LN -s /etc/systemd/system/vjezd.service \
		$mntdir/p2/etc/systemd/system/multi-user.target.wants
	[ $? -ne 0 ] && error "cannot add vjezd.service to target. Exiting" 2
fi

# tcpgpio
$DRY_RUN rm $mntdir/p2/etc/systemd/system/tcpgpio.service \
	$mntdir/p2/etc/systemd/system/multi-user.target.wants/tcpgpio.service
if [ ! -z "$conf_run_tcpgpio" ]; then
	$DRY_RUN $LN -s /opt/vjezd/tcpgpio.service $mntdir/p2/etc/systemd/system
	[ $? -ne 0 ] && error "cannot link tcpgpio.service. Exiting" 2
	$DRY_RUN $LN -s /etc/systemd/system/tcpgpio.service \
		$mntdir/p2/etc/systemd/system/multi-user.target.wants
	[ $? -ne 0 ] && error "cannot add tcpgpio.service to target. Exiting" 2
fi

# mysql
$DRY_RUN rm $mntdir/p2/etc/systemd/system/mysql.service
if [ -z "$conf_run_mysql" ]; then
	# Mask mysql if it shouldn't run
	$DRY_RUN $LN -s /dev/null $mntdir/p2/etc/systemd/system/mysql.service
	[ $? -ne 0 ] && error "cannot mask mysql service. Exiting" 2
fi

# Configure network
echo Configuring network...
[ -z "$DRY_RUN" ] && echo "$IFACES_FILE" > $mntdir/p2/etc/network/interfaces
if [ ! -z "$RESOLV_FILE" ]; then
	[ -z $DRY_RUN ] && echo "$RESOLV_FILE" > $mntdir/p2/etc/resolv.conf
fi

# Configure application
echo Configuring application...
if [ ! -z "$conf_run_vjezd" ]; then
	[ -z $DRY_RUN ] && echo "$CONF_FILE" > $mntdir/p2/opt/vjezd/vjezd.conf
fi


# Cleanup
echo Waiting for sync...
$DRY_RUN $SYNC
sleep 5

if [ -z "$NO_UMOUNT" ]; then
	# Unmount partitions
	echo Unmounting image partitions...
	for p in p1 p2 ; do
		$DRY_RUN $UMOUNT ${imgdev}${p}
		[ $? -ne 0 ] && error "Error unmounting ${imgdev}${p}. Exiting" 2
	done

	# Remove mapped partitions
	echo Removing image mapper...
	$DRY_RUN $KPARTX -d $IMG
else
	echo Not unmounting partitions. To unmount manually do:
	echo \# $UMOUNT ${imgdev}p1
	echo \# $UMOUNT ${imgdev}p2
	echo \# $KPARTX -d $IMG
fi

echo
echo Image was successfully created in: $IMG

exit 0
