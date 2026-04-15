`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2024/03/07 19:21:19
// Design Name: 
// Module Name: top
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

uart2spi(
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

*/

//功能：1、通过串口配置寄存器 2、上电默认配置寄存器  3、读取ADC数据 
module top(
    input rx_cn,//UART输入
    input clk,//时钟输入，100MHz
    input rst,
    output spi_le1,
    output spi_le2,
    output spi_data,
    output spi_clk,
    output sta_led,//常亮，用于确定状态是否为0
    output sel_led,//用于确定最后一次sel的值，为SPI设备1时亮起

    input spi_data_a_1,
    input spi_data_b_1,
    output spi_clk_1,
    output spi_cs_1,

    input spi_data_a_2,
    input spi_data_b_2,
    output spi_clk_2,
    output spi_cs_2,

    input muxout_pulse,


    //以下是读取信号
    output finish_1,
    output [15:0] data_a_1,
    output [15:0] data_b_1,
    output finish_2,
    output [15:0] data_a_2,
    output [15:0] data_b_2    
    

    );

    reg muxout;
    reg pre_muxout_pulse;
    always @(negedge clk or negedge rst) begin
        if(!rst)
        begin
            pre_muxout_pulse <= muxout_pulse;
            muxout<=0;
        end
        else
        begin
            pre_muxout_pulse <= muxout_pulse;
            if((!pre_muxout_pulse)&&(muxout_pulse))
            begin
                muxout<=!muxout;
            end
        end
    end




    spi_reg_config_top spi_reg_config_top1(
    .rx_cn(rx_cn),//UART输入
    .clk(clk),//时钟输入，100MHz
    .rst(rst),
    .spi_le1(spi_le1),
    .spi_le2(spi_le2),
    .spi_data(spi_data),
    .spi_clk(spi_clk),
    .sta_led(sta_led),//常亮，用于确定状态是否为0
    .sel_led(sel_led)//用于确定最后一次sel的值，为SPI设备1时亮起
    );

    /*
    module spi_read_2bit(
    input rst,
    input clk,
    input spi_data_a,
    input spi_data_b,
    output spi_clk,
    output reg spi_cs,
    output reg finish,//上升沿即读取完成
    output reg [15:0] data_a,
    output reg [15:0] data_b
    );
    */

    wire clk_33M;
    div_100M_33M  div_100M_33M1
    (
    // Clock out ports
    .clk_33M(clk_33M),
    // Status and control signals
    .resetn(rst),
    // Clock in ports
    .clk(clk)
    );


    spi_read_2bit spi_read_2bit1(
        .rst(rst),
        .clk(clk_33M),
        .spi_data_a(spi_data_a_1),
        .spi_data_b(spi_data_b_1),
        .spi_clk(spi_clk_1),
        .spi_cs(spi_cs_1),
        .finish(finish_1),
        .data_a(data_a_1),
        .data_b(data_b_1),
        .muxout(muxout)
    );



    wire finish_2;
    wire [15:0] data_a_2;
    wire [15:0] data_b_2;
    spi_read_2bit spi_read_2bit2(
        .rst(rst),
        .clk(clk_33M),
        .spi_data_a(spi_data_a_2),
        .spi_data_b(spi_data_b_2),
        .spi_clk(spi_clk_2),
        .spi_cs(spi_cs_2),
        .finish(finish_2),
        .data_a(data_a_2),
        .data_b(data_b_2),
        .muxout(muxout)
    );  



endmodule
