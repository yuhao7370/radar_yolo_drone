`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2024/03/07 18:53:23
// Design Name: 
// Module Name: uart_rec
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

module uart_rec(clk,rst,data,start,ready,rx_cn);//每次收到结束位，ready产生一次上升延，受到起始位则产生一次下降沿


input clk;
input rst;
output reg[7:0]data;
output reg start;
output reg ready;

input rx_cn;


parameter rate=163;//16倍波特率分频比
reg baud_clk;
reg [7:0]baud_cnt;
reg [8:0]sta;//状态


always@(negedge clk or negedge rst)
    begin
    if(!rst)
    begin
    baud_clk=0;
    baud_cnt=0;
    end
    else
    begin
    baud_cnt=baud_cnt+1;
    if(baud_cnt==rate/2)
    begin
    baud_clk=!baud_clk;
    baud_cnt=0;
    end
    end
end
reg rx_cn_reg;
always@(negedge baud_clk or negedge rst)
begin
    if(!rst)
    begin
        sta=0;
        ready=1;
        start=0;
        data=0;
        rx_cn_reg = rx_cn;
    end
    else 
    if(sta>0)
    begin
        sta=sta+1;
        if(sta%16==8)
        begin
        if(sta/16>0)
            begin
            if(sta/16==9)
            begin
                start=0;
                sta=0;
                ready=1;
            end
            else
                data[sta/16-1]=rx_cn;
            end

        end

    end

    else 
    if(rx_cn_reg == 1 &&rx_cn == 0)
    begin
        sta=1;
        ready=0;
        start=1;
    end
    rx_cn_reg = rx_cn;

end


endmodule