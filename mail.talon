app.app: mail
-

archive: key(ctrl-cmd-a)
junk: key(cmd-shift-j)
download: user.mail_download_images()
reply: key(cmd-r)
reply all: key(cmd-shift-r)
forward: key(cmd-shift-f)

mark [as] read: user.mail_mark_as_read()
mark [as] unread: user.mail_mark_as_unread()

send [this] message: key(cmd-shift-d)

next: user.mail_select_message(1)
previous: user.mail_select_message(-1)

goneck: user.mail_select_unread_message()
go next: user.mail_select_unread_message()
