`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2024/03/09 13:13:51
// Design Name: 
// Module Name: uart2spi
// Project Name: 
// Target Devices: 
// Tool Versions: 
// Description: 
// 
// Dependencies: 
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
//////////////////////////////////////////////////////////////////////////////////

/*
作用：接收UART数据，每接收完一帧便配置到SPI
数据帧格式：五字节一帧：（1）sel选择器件，0为ADF415X，1为MMIC   （2）SPI字节最高位  （3）SPI字节第二高位  （4）SPI字节第二低位  （5）SPI字节最低位
注意：输入频率必须为100MHz，输入后会被四分频为25MHz分别提供UART、SPI。UART波特率为9600，SPI时钟频率为12.5MHz
*/
module uart2spi(
    input rx_cn,//UART输入
    input clk,//时钟输入，100MHz
    input rst,
    output spi_le1,
    output spi_le2,
    output spi_data,
    output spi_clk,
    output reg sta_led,//常暗，用于确定状态是否为0，接收到UART数据时会短暂亮起。长时间亮起时表示UART数据接收出错，需要手动复位RST
    output  sel_led//用于确定最后一次sel的值，为SPI设备1时亮起
    );

    wire clk_div_4;

    div_4 div_4_1(
        .clk(clk),
        .rst(rst),
        .clk_div_4(clk_div_4)
    );

    
    reg [31:0] to_send;
    reg start;
    wire finish;
    reg sel;
    assign sel_led = sel;

    spi_write spi1(
        .data(to_send),
        .clk(clk_div_4),
        .rst(rst),
        .start(start),
        .finish(finish),
        .spi_le1(spi_le1),
        .spi_le2(spi_le2),
        .sel(sel),
        .spi_data(spi_data),
        .spi_clk(spi_clk)
    );

    wire [7:0] rec_data;
    wire uart_start;
    wire uart_ready;

    uart_rec uart_rec1(
        .clk(clk_div_4),
        .rst(rst),
        .data(rec_data),
        .start(uart_start),
        .ready(uart_ready),
        .rx_cn(rx_cn)
        );

    reg [3:0] sta;//状态

    always @(posedge uart_ready or negedge rst) begin
        if(rst==0)
        begin
            sta <= 0;
            start <= 1;
            sel <= 0;
            to_send <= 0;
            sta_led <=0 ;
        end
        else
        begin
            if(sta==0)//接收到sel字节
            begin
                sta_led <= 1;
                sel <= rec_data[0];
                sta <= sta+1;
                start <= 1;
            end
            else if(sta>=1 && sta<=4)
            begin
                sta_led <= 1;
                to_send[(39-8*sta) -:8] <= rec_data;
                //to_send[7:0] <= rec_data;
                sta <= sta+1;
                if(sta == 4)//收完sel与4个字节
                begin
                    start <= 0;//开始发送SPI
                    sta <= 0;//进入下一次循环
                    sta_led <= 0;
                end
            end
            else
            begin
                sta <= 0;
                start <= 1;
                sel <= 0;
                to_send <= 0;
                sta_led <=0 ;
            end
            
            
        end
        
    end

endmodule

