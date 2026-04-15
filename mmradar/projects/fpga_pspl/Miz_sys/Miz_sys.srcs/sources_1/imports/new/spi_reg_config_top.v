`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2024/03/10 12:16:47
// Design Name: 
// Module Name: spi_reg_config_top
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



//功能：1、通过串口配置寄存器 2、上电默认配置寄存器 
module spi_reg_config_top(
    input rx_cn,//UART输入
    input clk,//时钟输入，100MHz
    input rst,
    output spi_le1,
    output spi_le2,
    output spi_data,
    output spi_clk,
    output sta_led,//常亮，用于确定状态是否为0
    output  sel_led//用于确定最后一次sel的值，为SPI设备1时亮起
    );


    wire uart2spi_le1;
    wire uart2spi_le2;
    wire uart2spi_data;
    wire uart2spi_clk;

    uart2spi uart2spi1(
        .rx_cn(rx_cn),
        .clk(clk),
        .rst(rst),
        .spi_le1(uart2spi_le1),
        .spi_le2(uart2spi_le2),
        .spi_data(uart2spi_data),
        .spi_clk(uart2spi_clk),
        .sta_led(sta_led),
        .sel_led(sel_led)
    );




    wire clk_div_4;

    div_4 div_4_1(
        .clk(clk),
        .rst(rst),
        .clk_div_4(clk_div_4)
    );


    wire autospi_le1;
    wire autospi_le2;
    wire autospi_data;
    wire autospi_clk;

    autospi autospi1(
        .clk(clk_div_4),
        .rst(rst),
        .spi_le1(autospi_le1),
        .spi_le2(autospi_le2),
        .spi_data(autospi_data),
        .spi_clk(autospi_clk)
    );

    


    assign spi_le1  = uart2spi_le1  & autospi_le1;
    assign spi_le2  = uart2spi_le2  & autospi_le2; 
    assign spi_data = uart2spi_data & autospi_data;
    assign spi_clk  = uart2spi_clk  | autospi_clk;


endmodule
