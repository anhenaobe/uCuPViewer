/* Milk-V Duo S: maestro SPI modo 0 por sysfs GPIO (sin /dev/spidev).
 * SPI frame of exactly 264 bytes on stdout, timing stats on stderr.
 * Compile: gcc -O2 -std=c11 -D_DEFAULT_SOURCE -Wall -Wextra spi_master.c -o spi_master
 * Usage: sudo ./spi_master 2 > frame.bin
 */
#define _DEFAULT_SOURCE
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>
#include <fcntl.h>
#include <string.h>
#include <errno.h>

#define LEN 264
static int mo=-1,mi=-1,ck=-1,cs=-1;
static long half_us=200;
static void die(const char *s){perror(s);exit(2);}
static int pin_open(int n,int rw) {
    char path[128];snprintf(path,sizeof path,"/sys/class/gpio/gpio%d/value",n);
    int fd=open(path,rw?O_WRONLY:O_RDONLY);
    if(fd<0){fprintf(stderr,"Error abriendo GPIO %d. Ejecuta preparar_gpio.sh\n",n);die(path);}
    return fd;
}
static void set(int fd,int val) {
    if(lseek(fd,0,SEEK_SET)<0)die("lseek gpio");
    if(write(fd,val?"1":"0",1)!=1)die("write gpio");
}
static int get(int fd) {
    char c='0';
    if(lseek(fd,0,SEEK_SET)<0)die("lseek gpio");
    if(read(fd,&c,1)!=1)die("read gpio");
    return c=='1';
}
static void delay(void){
    struct timespec t={half_us/1000000,(half_us%1000000)*1000};
    while(nanosleep(&t,&t)<0 && errno==EINTR){}
}
static double mono(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec+t.tv_nsec*1e-9;}
int main(int argc,char **argv){
    if(argc<2 || argc>3){fprintf(stderr,"Uso: spi_master PRESET(1-3) [half_us >=100]\n");return 2;}
    int preset=atoi(argv[1]);
    if(preset<1||preset>3){fprintf(stderr,"Preset inválido\n");return 2;}
    if(argc==3){half_us=atol(argv[2]);if(half_us<100||half_us>1000){fprintf(stderr,"half_us entre 100 y 1000\n");return 2;}}
    mo=pin_open(461,1);mi=pin_open(462,0);ck=pin_open(463,1);cs=pin_open(464,1);
    uint8_t rx[LEN]={0};
    set(cs,1);set(ck,0);set(mo,0);usleep(20000);
    double start=mono();
    set(cs,0);usleep(15000); /* STM32 EXTI tiene margen para preparar el primer bit */
    for(int i=0;i<LEN;i++){
        uint8_t cmd=(i==0)?(uint8_t)preset:0u;
        uint8_t value=0;
        for(int bit=7;bit>=0;bit--){
            set(mo,(cmd>>bit)&1);delay();
            set(ck,1);delay();
            value=(uint8_t)((value<<1)|get(mi));
            set(ck,0);delay();
        }
        rx[i]=value;
    }
    set(cs,1);set(ck,0);set(mo,0);
    double elapsed=mono()-start;
    fprintf(stderr,"SPI SW: %d bytes en %.3f s, %.0f bits/s efectivos\n",LEN,elapsed,LEN*8/elapsed);
    if(fwrite(rx,1,LEN,stdout)!=LEN)die("write stdout");
    fflush(stdout);
    close(mo);close(mi);close(ck);close(cs);
    return 0;
}
