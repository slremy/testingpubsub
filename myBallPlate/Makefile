CC=gcc
CFLAGS=-I.

all: cudp ctcp curl judp jtcp jurl

cudp: nlcontrollerudp.c
	$(CC) nlcontrollerudp.c -o cnlcontrollerudp -lm
ctcp: nlcontrollertcp.c
	$(CC) nlcontrollertcp.c -o cnlcontrollertcp -lm
curl: nlcontroller.c
	$(CC) nlcontroller.c -o cnlcontroller -lm -lcurl
judp: nlcontrollerudp.java
	javac nlcontrollerudp.java
jtcp: nlcontrollertcp.java
	javac nlcontrollertcp.java
jurl: nlcontroller.java
	javac nlcontroller.java
