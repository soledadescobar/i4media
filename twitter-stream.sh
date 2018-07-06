#!/bin/sh

### BEGIN INIT INFO
# Provides:          i4media.twitter-stream
# Required-Start:    $remote_fs $syslog
# Required-Stop:     $remote_fs $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: i4media twitter streaming service
# Description:       Services Provided: Streaming, Updater, Bridge (5501)
### END INIT INFO

DIR=/usr/lib/i4media/i4media
DAEMON=${DIR}/control.py
DAEMON_NAME=i4media.twitter-stream
DAEMON_OPTS="--stream"
DAEMON_USER=root

PID_FILE=/var/run/${DAEMON_NAME}.pid

. /lib/lsb/init-functions

do_start () {
    log_daemon_msg "Starting $DAEMON_NAME with options $DAEMON_OPTS"
    start-stop-daemon --start --background --oknodo --pidfile ${PID_FILE} --make-pidfile --user ${DAEMON_USER} --chuid ${DAEMON_USER} --startas ${DAEMON} -- ${DAEMON_OPTS}
    log_end_msg $?
}
do_stop () {
    log_daemon_msg "Stopping system $DAEMON_NAME daemon"
    start-stop-daemon --stop --pidfile ${PID_FILE} --retry 10
    log_end_msg $?
}

case "$1" in

    start|stop)
        do_${1}
        ;;

    restart|reload|force-reload)
        do_stop
        do_start
        ;;

    status)
        status_of_proc "$DAEMON_NAME" "$DAEMON" && exit 0 || exit $?
        ;;

    *)
        echo "Usage: /etc/init.d/$DAEMON_NAME {start|stop|restart|status}"
        exit 1
        ;;

esac
exit 0
