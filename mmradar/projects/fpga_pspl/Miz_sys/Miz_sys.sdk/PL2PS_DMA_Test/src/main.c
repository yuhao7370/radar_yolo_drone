
/*
 *
 * www.osrc.cn
 * copyright by liyang mi lian dian zi www.osrc.cn
 * axi dma test
 *
*/


#include "dma_intr.h"
#include "timer_intr.h"
#include "sys_intr.h"
#include "xgpio.h"
#include "ff.h"
#include "xsdps.h"
#include "xparameters.h"
#include <stdio.h>
#include "xil_printf.h"
#include "lwip/err.h"
#include "lwip/tcp.h"
#include "lwipopts.h"
#include "netif/xadapter.h"
#include "lwip/ip.h"
#include "lwip/ip_addr.h"
#include "lwip/init.h"
#include "lwip/dhcp.h"
#include <string.h>


static XScuGic Intc; //GIC
static  XAxiDma AxiDma;
static  XScuTimer Timer;//timer

volatile u32 RX_success;
volatile u32 TX_success;

volatile u32 RX_ready=1;
volatile u32 TX_ready=1;

#define TIMER_LOAD_VALUE    166666665 //0.5S

#define buf_cnt 4
#define BUFFER_BASE TX_BUFFER_BASE


int i;
int Index;
u8 *TxBufferPtr= (u8 *)TX_BUFFER_BASE;
u8 *RxBufferPtr=(u8 *)RX_BUFFER_BASE;
u8 *data_buf[buf_cnt];
u8 Value=0;
float speed_tx;
float speed_rx;
static XGpio Gpio;

#define AXI_GPIO_DEV_ID	        XPAR_AXI_GPIO_0_DEVICE_ID

static FATFS SD_Dev; // File System instance
char *SD_Path = "0:/"; // string pointer to the logical drive number
static char FileName[32] = "sar.bin"; // name of the log
FIL file;

int SD_init()
{
FRESULT result;
//-----------------------mount dev-----------------------------------------------
result = f_mount(&SD_Dev,SD_Path, 0);
if (result != 0) {
return XST_FAILURE;
}
return XST_SUCCESS;
}
int file_open()
{
	 FRESULT result;
	 result=f_open(&file,FileName,FA_CREATE_ALWAYS | FA_WRITE);
	 if (result != 0) {
	 return XST_FAILURE;
	 }
	 f_lseek(&file, 0);
	 return XST_SUCCESS;
}
void file_write(char* dat,u32 len)
{
	 UINT BytesWr;
	 f_write(&file,(void*) dat,len,&BytesWr);
}
void file_close()
{
	f_close(&file);
}


int axi_dma_test()
{
	int Status;
	char speed_r;
	char speed_t;
	TxDone = 0;
	RxDone = 0;
	Error = 0;


	xil_printf( "----DMA Test----\r\n");

	//xil_printf("PKT_LEN=%d\r\n",MAX_PKT_LEN);

	//for(Index = 0; Index < MAX_PKT_LEN; Index ++) {
	//		TxBufferPtr[Index] = 0x00;


	//}
	/* Flush the SrcBuffer before the DMA transfer, in case the Data Cache
	 * is enabled
	 */
	//Xil_DCacheFlushRange((u32)TxBufferPtr, MAX_PKT_LEN);
	//Timer_start(&Timer);

	//if(SD_init()==XST_SUCCESS)
	//{
	//	xil_printf( "open sd success\r\n");

	//}
	//else
	//{
	//	xil_printf( "open sd failed!!!\r\n");
	//}

	//if(file_open()==XST_SUCCESS)
	//{
	//	xil_printf( "open file success\r\n");

	//}
	//else
	//{
	//	xil_printf( "open file failed!!!\r\n");
	//}

	XGpio_DiscreteWrite(&Gpio, 1, 1);

#define dat_cnt (10240*4)//512�β���
#define dot_num 20

	XGpio_DiscreteWrite(&Gpio, 1, 1);







	//char* data_buff=malloc(40960000);
	char* data_buff[dot_num];
	for(int i=0;i<dot_num;i++)
	{
		data_buff[i]=malloc(dat_cnt);
	}
	xil_printf( "going\r\n");
	while(1)
	//for(i = 0; i < Tries; i ++)
	{



		   Status = XAxiDma_SimpleTransfer(&AxiDma,(u32)RxBufferPtr,
					(u32)(dat_cnt), XAXIDMA_DEVICE_TO_DMA);
		while(Status!=XST_SUCCESS)
		{
			 Status = XAxiDma_SimpleTransfer(&AxiDma,(u32)RxBufferPtr,
								(u32)(dat_cnt), XAXIDMA_DEVICE_TO_DMA);
		}

		Xil_DCacheInvalidateRange((u32)RxBufferPtr, (u32)dat_cnt);

			//if(RX_success>=200)
				//{putchar(0xAB);putchar(0xCD);RX_success=0;}
			//for(int i=0;i<8;i++)
			//{
			//	printf("%X,",RxBufferPtr[i]);
			//}
			//printf("\r\n");


			//file_write(RxBufferPtr,dat_cnt);
		for(int i=0;i<dat_cnt;i++)
		{
			data_buff[RX_success][i]=RxBufferPtr[i];
		}

			RX_success++;
			if(RX_success>=dot_num)
			{

				xil_printf( "stop \r\n");
				if(SD_init()==XST_SUCCESS)
				{
					xil_printf( "open sd success\r\n");

				}
				else
				{
					xil_printf( "open sd failed!!!\r\n");
				}

				if(file_open()==XST_SUCCESS)
				{
					xil_printf( "open file success\r\n");

				}
				else
				{
					xil_printf( "open file failed!!!\r\n");
				}
				for(int i=0;i<dot_num;i++)
				{
					file_write(data_buff[i],dat_cnt);
				}

				file_close();
				xil_printf( "write sd success\r\n");
				break;

			}






	}

	/* Disable TX and RX Ring interrupts and return success */
	DMA_DisableIntrSystem(&Intc, TX_INTR_ID, RX_INTR_ID);
Done:
	xil_printf("--- Exiting Test --- \r\n");

	return XST_SUCCESS;

}

int init_intr_sys(void)
{
	DMA_Intr_Init(&AxiDma,0);//initial interrupt system
	Timer_init(&Timer,TIMER_LOAD_VALUE,0);
	Init_Intr_System(&Intc); // initial DMA interrupt system
	Setup_Intr_Exception(&Intc);
	DMA_Setup_Intr_System(&Intc,&AxiDma,TX_INTR_ID,RX_INTR_ID);//setup dma interrpt system
	Timer_Setup_Intr_System(&Intc,&Timer,TIMER_IRPT_INTR);
	DMA_Intr_Enable(&Intc,&AxiDma);

}
struct netif *netif, server_netif;
struct ip_addr ipaddr, netmask, gw;
unsigned char mac_ethernet_address[] = { 0x00, 0x0a, 0x35, 0x00, 0x01, 0x03 };
void eth_init(void)
{

	

	/* the mac address of the board. this should be unique per board */
	
	netif = &server_netif;
	IP4_ADDR(&(ipaddr.u_addr.ip4), 192, 168, 1, 11);
	IP4_ADDR(&(netmask.u_addr.ip4), 255, 255, 255, 0);
	IP4_ADDR(&(gw.u_addr.ip4), 192, 168, 1, 11);
	lwip_init();
	if (!xemac_add(netif, &ipaddr, &netmask, &gw, mac_ethernet_address, XPAR_XEMACPS_0_BASEADDR)) {
	xil_printf("Error adding N/W interface\r\n");
	}

	netif_set_default(netif);
	netif_set_up(netif);

	xil_printf("eth_init finished \r\n");

}
u16_t port;
struct ip_addr ipaddress;
struct tcp_pcb *request_pcb;
struct tcp_pcb *connected_pcb;
volatile unsigned tcp_client_connected;
volatile unsigned connecting;
volatile int tcp_trans_done;


/*this fuction just used to count the tcp transmission times*/
static err_t;


volatile int start=0;
volatile int stop=0;	
//int going=0;
tcp_sent_callback(void *arg, struct tcp_pcb *tpcb, u16_t len)
{

	err_t err;
	tcp_trans_done = 1;
	err = tcp_output(tpcb);
	if (err != ERR_OK) {
		xil_printf("txperf: Error on tcp_output: %d\r\n",err);
		return -1;
	}

	return ERR_OK;
}
err_t tcp_recv_callback(void *arg, 
                              struct tcp_pcb *tpcb, 
                              struct pbuf *p, 
                              err_t err)
{
	static char recv_test_buf[20];
	    if (p != NULL)
    {
        struct pbuf *q;
        int recv_count = 0;

        tcp_recved(tpcb, p->tot_len);  /* 更新接收窗口 */
        for (q = p; q != NULL; q = q->next)
        {
            if (q->len > sizeof(recv_test_buf))
            {
                memcpy(recv_test_buf, q->payload, sizeof(recv_test_buf));
                break;
            }
            else 
            {
                if (recv_count >= sizeof(recv_test_buf))
                    break;
                memcpy(&recv_test_buf[recv_count], q->payload, q->len);
                recv_count += q->len;
            }
        }
        pbuf_free(p);
    }
    else if (err == ERR_OK) /* 接收成功但数据包是空的说明客户端断开连接 */
    {
        xil_printf("客户端断开连接\r\n");
		tcp_client_connected=0;
        return tcp_close(tpcb);
    }

    struct ip4_addr_fmt *ip = (struct ip4_addr_fmt *)&tpcb->remote_ip;
    xil_printf("msg %s\r\n",recv_test_buf);
	if(strcmp(recv_test_buf,"start")==0)
	{
		start=1;
		xil_printf("start collecting\r\n");
	}
	else if(strcmp(recv_test_buf,"stop")==0)
	{
		stop=1;
		xil_printf("stop collecting\r\n");
	}	
	else
	{
		start=1;
	}
    memset(recv_test_buf, 0, sizeof(recv_test_buf));

    return ERR_OK;  /* 记得return ERR_OK,很重要/(ㄒoㄒ)/~~ */


}
void tcp_err_callback(void *arg, err_t err)
{
	xil_printf("ERR!!%d\r\n",err);
	connecting=0;
	tcp_client_connected=0;
	stop=1;
}


tcp_connected_callback(void *arg, struct tcp_pcb *tpcb, err_t err)
{
	if (err == ERR_OK)
	{

		xil_printf("txperf: Connected to iperf server\r\n");

		/* store state */
		connected_pcb = tpcb;

		/* set callback values & functions */
		tcp_arg(tpcb, NULL);
		tcp_sent(tpcb, tcp_sent_callback);
		//tcp_recv(struct tcp_pcb *pcb, tcp_recv_fn recv)
		tcp_recv(tpcb, tcp_recv_callback);
		

		/* disable nagle algorithm to ensure
		* the last small segment of a ADC packet will be sent out immediately
		* with no delay
		* */
		tcp_nagle_disable(tpcb);

		if(!tcp_nagle_disabled(tpcb))
			xil_printf("tcp nagle disable failed!\r\n");

		tcp_client_connected = 1;

		/* initiate data transfer */	
	}
	else
	{
		xil_printf("connect failed!\r\n");
	}
	connecting=0;
	return ERR_OK;
}


void send_init(void)
{


		err_t err;


		/* create new TCP PCB structure */
		request_pcb = tcp_new();
		if (!request_pcb) {
			xil_printf("txperf: Error creating PCB. Out of Memory\r\n");
			return -1;
		}

		/* connect to iperf tcp server */
		IP4_ADDR(&(ipaddress.u_addr.ip4),  192, 168, 1, 2);		/* iperf server address */

		port = 2829;					/* iperf default port */


	    tcp_trans_done = 1;


		err = tcp_connect(request_pcb, &ipaddress, port, tcp_connected_callback);
		tcp_err(request_pcb, tcp_err_callback);
		if (err != ERR_OK) {
			xil_printf("txperf: tcp_connect returned error: %d\r\n", err);
		}
		tcp_client_connected=0;
		connecting=1;
		connected_pcb=request_pcb;


}

int tcp_send(char* dat,u32 len)
{
	err_t err;
	struct tcp_pcb *tpcb = connected_pcb;
	int buf_len=tcp_sndbuf(tpcb);
	if (tcp_sndbuf(tpcb) > len)
	{
		/*transmit received data through TCP*/
		err = tcp_write(tpcb, dat, len, TCP_WRITE_FLAG_MORE);
		if (err != ERR_OK) {
			xil_printf("txperf: Error on tcp_write: %d\r\n", err);
			connected_pcb = NULL;
			return -1;
		}
		
		err = tcp_output(tpcb);
		if (err != ERR_OK) {
			xil_printf("txperf: Error on tcp_output: %d\r\n",err);
			return -1;
		}
		return 0;
	}
	else
	{
		//xil_printf("buffer not enough!leaft %d\r\n",buf_len);
		return -1;

	}
}

// int main(void)
// {
// 	xil_printf("Come!!!!!!!!!!!!! \r\n");
// 	XGpio_Initialize(&Gpio, AXI_GPIO_DEV_ID);
// 	XGpio_SetDataDirection(&Gpio, 1, 0);//输出模式
// 	XGpio_DiscreteWrite(&Gpio, 1, 0);
// 	init_intr_sys();


// 	sleep(5);
// 	u8* dat=0;

// 	int Status;


// 	XGpio_DiscreteWrite(&Gpio, 1, 1);//输出1

// 	//空读一次
// 	dat=(u8*)(BUFFER_BASE);
// 		Status = XAxiDma_SimpleTransfer(&AxiDma,(u32)(dat),
// 		(u32)(dat_cnt), XAXIDMA_DEVICE_TO_DMA);
// 	while(Status!=XST_SUCCESS)
// 	{
// 			Status = XAxiDma_SimpleTransfer(&AxiDma,(u32)(dat),
// 							(u32)(dat_cnt), XAXIDMA_DEVICE_TO_DMA);
// 	}

// 	while(!RxDone);
// 	Xil_DCacheInvalidateRange((u32)(dat), (u32)dat_cnt);


// 	xil_printf("start collect!!!!!!!!!!!!! \r\n");
// 	for(int i=0;i<900;i++)
// 	{
// 		dat=(u8*)(BUFFER_BASE+dat_cnt*i);
// 		Status = XAxiDma_SimpleTransfer(&AxiDma,(u32)(dat),
// 			(u32)(dat_cnt), XAXIDMA_DEVICE_TO_DMA);
// 		while(Status!=XST_SUCCESS)
// 		{
// 				Status = XAxiDma_SimpleTransfer(&AxiDma,(u32)(dat),
// 								(u32)(dat_cnt), XAXIDMA_DEVICE_TO_DMA);
// 		}

// 		while(!RxDone);
// 		Xil_DCacheInvalidateRange((u32)(dat), (u32)dat_cnt);
// 	}
// 	xil_printf("start write SD! \r\n");
// 	SD_init();
// 	file_open();
// 	for(int i=0;i<900;i++)
// 	{
// 		dat=(u8*)(BUFFER_BASE+dat_cnt*i);
// 		file_write(dat,(u32)dat_cnt);
// 	}
// 	file_close();
// 	xil_printf("Over!! \r\n");



// }


#define fifo_base BUFFER_BASE
#define fifo_len (10*dat_cnt)
u32 fifo_write_pt=fifo_base;
u32 fifo_read_pt=fifo_base;
u32 fifo_size=0;
u32 fifo_signal_read_valid_size=0;
void fifo_init(void)
{
	fifo_write_pt=fifo_base;
	fifo_read_pt=fifo_base;
	fifo_size=0;
	fifo_signal_read_valid_size=0;
}
u32 fifo_get_push_pt(void)
{
	return fifo_write_pt;
}
void fifo_push_finished(void)
{
	fifo_size+=dat_cnt;
	fifo_write_pt+=dat_cnt;
	if((fifo_write_pt-fifo_base)>=fifo_len)
	{
		fifo_write_pt=fifo_base;
	}
}
u32 fifo_get_pop_pt(void)
{
	return fifo_read_pt;
}
u32 fifo_pop_finished(u32 len)
{
	fifo_read_pt+=len;
	fifo_size-=len;
	if(fifo_read_pt-fifo_base>=fifo_len)
	{
		fifo_read_pt-=fifo_len;
	}
}
u32 fifo_get_valid_size(void)
{
	fifo_signal_read_valid_size=(fifo_base+fifo_len)-fifo_read_pt;
	if(fifo_signal_read_valid_size>fifo_size)
	{
		fifo_signal_read_valid_size=fifo_size;
	}
	return fifo_signal_read_valid_size;
}




volatile int Status;
int main(void)
{
	xil_printf("Come!!!!!!!!!!!!! \r\n");
	XGpio_Initialize(&Gpio, AXI_GPIO_DEV_ID);
	XGpio_SetDataDirection(&Gpio, 1, 0);//输出模式
	XGpio_DiscreteWrite(&Gpio, 1, 0);
	init_intr_sys();

	

	Timer_start(&Timer);

	int wait_time=0;
	int err_time=0;
	int succ_time=0;
	int out_time=0;
	int succ_go_time=0;
	u8* dat=0;


	volatile int going=0;
	volatile int wait_for_rec=0;
	u32 single_wait_time=0;
	u32 byte_cnt=0;
	u32 err_pack_time=0;
	sleep(4);
	eth_init();
	sleep(6);
	send_init();
	tcp_client_connected=0;
	connecting=1;
	while(1)
	{
		static u32 delay_cnt=0;
		xemacif_input(netif);
		delay_cnt++;
		if(delay_cnt>300000)
		{
			delay_cnt=0;
			if(tcp_client_connected==0 && connecting==1)
			{				
				connecting=0;
			}
			
		}
		if(tcp_client_connected==0 && connecting==0)
		{
			tcp_close(connected_pcb);
			tcp_abort(connected_pcb);
			send_init();
			xil_printf("connecting! \r\n");
		}

		if(Error)
		{
			Error=0;
			xil_printf("error!!");
		}

		if(usec>=2)
		{
			usec=0;
			//xil_printf("stop,wait:%d,succ:%d,out:%d,go=%d,byte=%d,err_pack=%d\r\n",wait_time,succ_time,out_time,succ_go_time,byte_cnt,err_pack_time);
			wait_time=0;
			err_pack_time=0;
			succ_time=0;	
			out_time=0;		
			succ_go_time=0;	
		}

		if(start)
		{
			start=0;
			going=1;
			wait_for_rec=0;
			fifo_init();
			XGpio_DiscreteWrite(&Gpio, 1, 1);
		}

		if(stop)
		{
			stop=0;
			going=0;

		}

		if(going==1 && wait_for_rec==0)
		{
			dat=(u8*)fifo_get_push_pt();
			Status = XAxiDma_SimpleTransfer(&AxiDma,(u32)(dat),
				(u32)(dat_cnt+4), XAXIDMA_DEVICE_TO_DMA);
			// while(Status!=XST_SUCCESS)
			// {
			// 	Status = XAxiDma_SimpleTransfer(&AxiDma,(u32)(dat),
			// 						(u32)(dat_cnt+4), XAXIDMA_DEVICE_TO_DMA);
			// 	err_time=1;
			// }
			if(Status!=XST_SUCCESS)
			{
				err_pack_time++;
			}
			err_time=0;
			wait_for_rec=1;
			single_wait_time=0;
			succ_go_time++;

		}

		if(wait_for_rec==1)
		{
			if(RxDone)
			{
				RxDone=0;
				Xil_DCacheInvalidateRange((u32)(dat), (u32)dat_cnt);
				succ_time++;
				wait_for_rec=0;
				fifo_push_finished();
			}
			else
			{
				wait_time++;
				single_wait_time++;
				if(single_wait_time>90000)
				{
					out_time++;
					wait_for_rec=0;

				}
			}
			
		}
		u32 valid_size=fifo_get_valid_size();
		if(valid_size!=0)
		{
			// fifo_get_pop_pt();
			// fifo_pop_finished(valid_size);
			// byte_cnt+=valid_size;

			if(tcp_client_connected)
			{
				u32 send_size=tcp_sndbuf(connected_pcb);
				if(valid_size<send_size)
				{
					send_size=valid_size;
				}	
				if(send_size>10)
				{
					send_size-=10;
				}
				if(send_size!=0)
				{
					
					if(tcp_send(fifo_get_pop_pt(),send_size)==0)
					{
						fifo_pop_finished(send_size);
						byte_cnt+=send_size;
						
					}					
				}

			}


		}







	}




}










// //完全正常的main
// int main(void)
// {
// 	xil_printf("Come!!!!!!!!!!!!! \r\n");
// 	XGpio_Initialize(&Gpio, AXI_GPIO_DEV_ID);
// 	XGpio_SetDataDirection(&Gpio, 1, 0);//输出模式
// 	XGpio_DiscreteWrite(&Gpio, 1, 0);
// 	init_intr_sys();


// 	u8* dat=0;
// 	xil_printf("start collect!!!!!!!!!!!!! \r\n");
// 	int Status;


// 	XGpio_DiscreteWrite(&Gpio, 1, 1);//输出1
// 	Timer_start(&Timer);

// 	int wait_time=0;
// 	int err_time=0;
// 	int succ_time=0;

// 	while(1)
// 	{
// 		dat=(u8*)(BUFFER_BASE);
// 		Status = XAxiDma_SimpleTransfer(&AxiDma,(u32)(dat),
// 			(u32)(dat_cnt), XAXIDMA_DEVICE_TO_DMA);
// 		while(Status!=XST_SUCCESS)
// 		{
// 				Status = XAxiDma_SimpleTransfer(&AxiDma,(u32)(dat),
// 								(u32)(dat_cnt), XAXIDMA_DEVICE_TO_DMA);
// 				err_time++;
				
// 		}
// 		succ_time++;

// 		while(!RxDone)
// 		{
// 			wait_time++;
// 		}
// 		RxDone=0;
// 		Xil_DCacheInvalidateRange((u32)(dat), (u32)dat_cnt);
// 		if(usec>=2)
// 		{
// 			usec=0;
// 			xil_printf("%d,%d,%d\r\n",wait_time,err_time,succ_time);
// 			wait_time=0;
// 			err_time=0;
// 			succ_time=0;
// 		}
// 	}

// }













// int main(void)
// {
// 	xil_printf("Come!!!!!!!!!!!!! \r\n");
// 	XGpio_Initialize(&Gpio, AXI_GPIO_DEV_ID);
// 	XGpio_SetDataDirection(&Gpio, 1, 0);//输出模式
// 	XGpio_DiscreteWrite(&Gpio, 1, 0);
	
// 	init_intr_sys();

// 	eth_init();
// 	send_init();


// 	int Status;
// 	u32 cnt=0;

// 	XGpio_DiscreteWrite(&Gpio, 1, 0);//输出0
	


// 	for(int i=0;i<buf_cnt;i++)
// 	{
// 		data_buf[i]=(u8*)(BUFFER_BASE+dat_cnt*i);
// 	}
// 	int rec_buf_cnt=0;
// 	int send_buf_cnt=0;
// 	int delay_cnt=0;
// 	while(1)
// 	{
// 		xemacif_input(netif);
// 		delay_cnt++;
// 		if(delay_cnt>300000)
// 		{
// 			delay_cnt=0;
// 			if(tcp_client_connected==0 && connecting==1)
// 			{
// 				tcp_close(connected_pcb);
// 				tcp_abort(connected_pcb);
// 				connecting=0;
// 			}
			
// 		}

// 		if(tcp_client_connected==0 && connecting==0)
// 		{
// 			tcp_close(connected_pcb);
// 			tcp_abort(connected_pcb);
// 			send_init();
// 			xil_printf("connecting! \r\n");
// 		}

// 		if(start==1)
// 		{
// 			start=0;
// 			going=1;
// 			XGpio_DiscreteWrite(&Gpio, 1, 1);//输出1
// 		}
// 		if(stop==1)
// 		{
// 			stop=0;
// 			going=0;
// 			XGpio_DiscreteWrite(&Gpio, 1, 0);//输出0
// 		}
// 		if(going==1)
// 		{
// 		Status = XAxiDma_SimpleTransfer(&AxiDma,(u32)(data_buf[rec_buf_cnt]),
// 			(u32)(dat_cnt), XAXIDMA_DEVICE_TO_DMA);
// 		while(Status!=XST_SUCCESS)
// 		{
// 				Status = XAxiDma_SimpleTransfer(&AxiDma,(u32)(data_buf[rec_buf_cnt]),
// 								(u32)(dat_cnt), XAXIDMA_DEVICE_TO_DMA);
// 				xemacif_input(netif);
// 		}

// 		while(!RxDone);
// 		RxDone=0;
// 		Xil_DCacheInvalidateRange((u32)(data_buf[rec_buf_cnt]), (u32)dat_cnt);


// 		rec_buf_cnt++;
// 		if(rec_buf_cnt>=buf_cnt)
// 		{
// 			rec_buf_cnt=0;
// 		}
// 		if(tcp_client_connected)
// 		{
// 			send_buf_cnt=rec_buf_cnt-1;
// 			if(send_buf_cnt<0)
// 			{
// 				send_buf_cnt+=buf_cnt;
// 			}
// 			while(tcp_send((u32)(data_buf[send_buf_cnt]),dat_cnt)!=0)
// 			{
// 				xemacif_input(netif);
// 				tcp_output(connected_pcb);
// 			}
// 			cnt++;
// 			//if(cnt>=10)
// 			{
// 				tcp_output(connected_pcb);
// 				cnt=0;
// 			}

// 		}
// 		else
// 		{
// 			send_init();
// 			XGpio_DiscreteWrite(&Gpio, 1, 0);//输出0
// 			sleep(3);
// 			XGpio_DiscreteWrite(&Gpio, 1, 1);//输出1

// 		}
// 		}
		

// 	}



// }


