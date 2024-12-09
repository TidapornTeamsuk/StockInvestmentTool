''' pip install yfinance 
    pip install pillow
'''

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
from tkinter import *
from tkinter import ttk
from tkmacosx import Button
from PIL import Image, ImageTk
import datetime
import math

# Signal-based trading strategy functions with moving averages  
def strategySMA(data):
    sigPriceBuy = []
    sigPriceSell = []
    flag = -1

    # สร้างสัญญาณซื้อขายเมื่อเส้นค่าเฉลี่ย 30 และ 100 วันตัดกัน
    for i in range(len(data)):
        if data["SMA30"][i] > data["SMA100"][i]:
            if flag != 1:
                sigPriceBuy.append(data["Adj Close"][i])
                sigPriceSell.append(np.nan)
                flag = 1
            else:
                sigPriceBuy.append(np.nan)
                sigPriceSell.append(np.nan)
        elif data["SMA30"][i] < data["SMA100"][i]:
            if flag != 0:
                sigPriceBuy.append(np.nan)
                sigPriceSell.append(data["Adj Close"][i])
                flag = 0
            else:
                sigPriceBuy.append(np.nan)
                sigPriceSell.append(np.nan)
        else:
            sigPriceBuy.append(np.nan)
            sigPriceSell.append(np.nan)

    return (sigPriceBuy, sigPriceSell)

# Signal Based Trading Strategy Functions With Momentum (RSI)
def strategyRSI(data):

    sigPriceBuy = []
    sigPriceSell = []
    Loss = [0]
    Gain = [0]

    # การเปลี่ยนแปลงราคาวันนี้กับเมื่อวาน
    for i in range(1,len(data)):
        change = data["Close"][i] - data["Close"][i-1]
        if change < 0:
            Loss.append(abs(change))
            Gain.append(0)
        elif change > 0:
            Loss.append(0)
            Gain.append(change)
        else:
            Loss.append(0)
            Gain.append(0)

    data["Gain"] = Gain
    data["Loss"] = Loss
    AvgGain = []
    AvgLoss = []
    y70 = []
    y30 = []
    sumGain = 0
    sumLoss = 0

    # ค่าเฉลี่ยย้อนหลังของ 14 วันที่ขึ้นและลง (14 วัน ย้อนหลัง มีขึ้นและลงกี่วัน ก็ใช้ค่านั้นมาคำนวณ)
    for i in range(len(data)):
        y70.append(70)
        y30.append(30)
        if i < 14:
            AvgGain.append(0)
            AvgLoss.append(0)
        elif i == 14:
            for j in range(14):
                sumGain += data["Gain"][j]
                sumLoss += data["Loss"][j]
            AvgGain.append(sumGain/14)
            AvgLoss.append(sumLoss/14)
        else:
            AvgGain.append((AvgGain[-1]*13 + data["Gain"][i])/14)
            AvgLoss.append((AvgLoss[-1]*13 + data["Loss"][i])/14)

    data["y70"] = y70
    data["y30"] = y30
    data["Avg Gain"] = AvgGain
    data["Avg Loss"] = AvgLoss

    data["RS"] = data["Avg Gain"]/data["Avg Loss"]
    data["RSI"] = 100 - (100 / (1 + data["RS"]))

    sigPriceBuy.append(np.nan)
    sigPriceSell.append(np.nan)
    flag = False
    flag2 = False

    # สร้างสัญญาณซื้อเมื่อความชันของเส้น RSI >= 13 และขายเมื่อเส้น RSI ขึ้น >= 70 แล้วลงมา <= 68.5
    for i in range(len(data)-1):
        if data["RSI"][i] <= 50 and data["RSI"][i+1] <= 50 and not flag:
            if data["RSI"][i+1] - data["RSI"][i] >= 13:
                sigPriceBuy.append(data["Adj Close"][i])
                sigPriceSell.append(np.nan)
                flag = True
            else:
                sigPriceBuy.append(np.nan)
                sigPriceSell.append(np.nan)

        elif flag:
            if data["RSI"][i] >= 70 or flag2:
                flag2 = True
                if data["RSI"][i] <= 68.5:
                    sigPriceBuy.append(np.nan)
                    sigPriceSell.append(data["Adj Close"][i])
                    flag = False
                    flag2 = False
                else:
                    sigPriceBuy.append(np.nan)
                    sigPriceSell.append(np.nan)
            else:
                sigPriceBuy.append(np.nan)
                sigPriceSell.append(np.nan)

        else:
            sigPriceBuy.append(np.nan)
            sigPriceSell.append(np.nan)

    return (sigPriceBuy, sigPriceSell)

# function when click "คำนวณผลตอบแทน"
def calculateProfit():
    try:
        # dowload stock data
        data = yf.download(input_stock.get()+".BK")
        data["SMA30"] = data["Adj Close"].rolling(window=30).mean()
        data["SMA100"] = data['Adj Close'].rolling(window=100).mean()

        # signals buy and sell moving averages strategy
        Buy_SellSMA = strategySMA(data)
        data['Buy Signal Price SMA'] = Buy_SellSMA[0]
        data['Sell Signal Price SMA'] = Buy_SellSMA[1]

        # signals buy and sell Momentum (RSI) strategy
        Buy_SellRSI = strategyRSI(data)
        data["Buy Signal Price RSI"] = Buy_SellRSI[0]
        data["Sell Signal Price RSI"] = Buy_SellRSI[1]

        buy = 0
        sell = 0
        totalStock = 0
        years = input_years.get()
        invesmentSMA = float(input_invesment.get())
        invesmentRSI = float(input_invesment.get())
        incomeSMA = invesmentSMA
        incomeRSI = invesmentRSI

        # calculate profit income SMA
        for i in range(len(data) - (365*years), len(data)):
            if math.isnan(data['Buy Signal Price SMA'][i]) == False:
                buy = (data['Buy Signal Price SMA'][i])
                totalStock = int(incomeSMA / buy)
                incomeSMA -= totalStock*buy
            if math.isnan(data['Sell Signal Price SMA'][i]) == False:
                sell = (data['Sell Signal Price SMA'][i])
                incomeSMA += totalStock*sell
                totalStock = 0
            currentPrice = data["Adj Close"][i]
        currentInvesmentSMA = incomeSMA + (totalStock*currentPrice)

        # calculate profit income RSI
        for i in range(len(data) - (365*years), len(data)):
            if math.isnan(data['Buy Signal Price RSI'][i]) == False:
                buy = (data['Buy Signal Price RSI'][i])
                totalStock = int(incomeRSI / buy)
                incomeRSI -= totalStock*buy
            if math.isnan(data['Sell Signal Price RSI'][i]) == False:
                sell = (data['Sell Signal Price RSI'][i])
                incomeRSI += totalStock*sell
                totalStock = 0
            currentPrice = data["Adj Close"][i]
        currentInvesmentRSI = incomeRSI + (totalStock*currentPrice)

        # show income and profit
        profitSMA = currentInvesmentSMA-invesmentSMA
        canvas.itemconfig(text_incomeSMA, text=("%.2f" % (currentInvesmentSMA)))
        canvas.itemconfig(text_profitSMA, text=("%.2f" % (profitSMA)))

        profitRSI = currentInvesmentRSI-invesmentRSI
        canvas.itemconfig(text_incomeRSI, text=("%.2f" % (currentInvesmentRSI)))
        canvas.itemconfig(text_profitRSI, text=("%.2f" % (profitRSI)))

        percentProfitSMA = profitSMA * 100 / float(input_invesment.get())
        percentProfitRSI = profitRSI * 100 / float(input_invesment.get())

        canvas.itemconfig(text_perProfitSMA, text="%.2f" %percentProfitSMA + " %")
        canvas.itemconfig(text_perProfitRSI, text="%.2f" %percentProfitRSI + " %")
        
        # profit comparison
        if percentProfitSMA < 0 and percentProfitRSI < 0:
            if percentProfitSMA > percentProfitRSI:
                canvas.itemconfig(text_profit3, text=("สัญญาณเส้นค่าเฉลี่ย"))
                canvas.itemconfig(text_profit4, text=("ขาดทุนน้อยกว่าอยู่ %.2f" % abs(percentProfitSMA - percentProfitRSI) + " %"))
            else:
                canvas.itemconfig(text_profit3, text=("สัญญาณโมเมนตัม"))
                canvas.itemconfig(text_profit4, text=("ขาดทุนน้อยกว่าอยู่ %.2f" % abs(percentProfitRSI - percentProfitSMA) + " %"))
        elif percentProfitSMA > percentProfitRSI:
            canvas.itemconfig(text_profit3, text=("สัญญาณเส้นค่าเฉลี่ย"))
            canvas.itemconfig(text_profit4, text=("ได้กำไรมากกว่าอยู่ %.2f" %(percentProfitSMA - percentProfitRSI) + " %"))
        elif percentProfitRSI > percentProfitSMA:
            canvas.itemconfig(text_profit3, text=("สัญญาณโมเมนตัม"))
            canvas.itemconfig(text_profit4, text=("ได้กำไรมากกว่าอยู่ %.2f" %(percentProfitRSI - percentProfitSMA) + " %"))
            
        global button_SMA, button_RSI

        # create button to show graph Buy&Sell Signals SMA
        button_SMA = Button(root, text="ดูสัญญาณการซื้อขาย", highlightbackground="#ffffff", bg="#3DDDCE", height=30, 
                            font=("Helvetica", 15), command=lambda: plot1(data))
        button_SMA = canvas.create_window(200, 447, anchor="n", window=button_SMA)

        # create button to show graph Buy&Sell Signals RSI
        button_RSI = Button(root, text="ดูสัญญาณการซื้อขาย", highlightbackground="#ffffff", bg="#3DDDCE", height=30, 
                            font=("Helvetica", 15), command=lambda: plot2(data))
        button_RSI = canvas.create_window(600, 447, anchor="n", window=button_RSI)

    except:
        canvas.itemconfig(text_profit3, text=("กรุณาใส่ข้อมูลใหม่อีกครั้ง"))
        canvas.itemconfig(text_profit4, text=(""))

        canvas.itemconfig(text_incomeSMA, text=(""))
        canvas.itemconfig(text_incomeRSI, text=(""))

        canvas.itemconfig(text_profitSMA, text=(""))
        canvas.itemconfig(text_profitRSI, text=(""))

        canvas.itemconfig(text_perProfitSMA, text=(""))
        canvas.itemconfig(text_perProfitRSI, text=(""))

        canvas.delete(button_RSI)
        canvas.delete(button_SMA)

# plot strategy1
def plot1(data):
    plt.figure(figsize=(12, 8))
    plt.plot(data["Adj Close"], 'steelblue', label=input_stock.get())
    plt.plot(data['SMA30'], 'tomato', label="SMA30")
    plt.plot(data['SMA100'], 'orange', label="SMA100",)
    plt.scatter(data.index, data["Buy Signal Price SMA"],label="Buy", marker='^', color="green")
    plt.scatter(data.index, data["Sell Signal Price SMA"],label="Sell", marker='v', color="red")
    plt.title("Simple moving average signals")
    plt.ylabel("Adj. Close Price (THB)")
    plt.legend(loc='upper left')
    plt.show()

# plot strategy2
def plot2(data):
    strategyRSI(data)
    print(data)
    plt.figure(figsize=(12, 8))
    plt.subplot(2, 1, 1)
    plt.title("RSI signals")
    plt.plot(data["Adj Close"], 'steelblue', label=input_stock.get())
    plt.scatter(data.index, data["Buy Signal Price RSI"], label="Buy", marker='^', color="green")
    plt.scatter(data.index, data["Sell Signal Price RSI"], label="Sell", marker='v', color="red")
    plt.ylabel("Adj. Close Price (THB)")
    plt.legend(loc='upper left')
    plt.subplot(2, 1, 2)
    plt.plot(data["RSI"], "steelblue", label="RSI")
    plt.plot(data["y70"], 'r--')
    plt.plot(data["y30"], "g--")
    plt.ylabel("RSI 14")
    plt.legend(loc='upper left')
    plt.show()

root = Tk()
root.title("Buy&Sell By Signals")
root.geometry("800x500+380+200")

background = PhotoImage(file="background.png")

# Create canvas
canvas = Canvas(root, width=500, height=500)
canvas.pack(fill="both", expand=True)
canvas.create_image(0, 0, image=background, anchor="nw")

# Define entry box (กล่องสำหรับ input)
input_stock = StringVar()
entry_stock = Entry(root, textvariable=input_stock, font=("Helvetica", 20), width=10, fg="black", bd=0)
entry_stock.insert(0, "Stocks...")

input_invesment = StringVar()
entry_invesment = Entry(root, textvariable=input_invesment, font=("Helvetica", 20), width=10, fg="black", bd=0)
entry_invesment.insert(0, "")

input_years = IntVar()
entry_years = Entry(root, textvariable=input_years, font=("Helvetica", 20), width=10, fg="black", bd=0)
entry_years.insert(0, "")

# Add entry boxes to the canvas
canvas.create_window(330, 35, anchor="n", window=entry_stock)
canvas.create_window(330, 75, anchor="n", window=entry_invesment)
canvas.create_window(330, 118, anchor="n", window=entry_years)

# Bind the entry boxs
entry_stock.bind("<Button-1>", lambda x: entry_stock.delete(0, "end"))
entry_invesment.bind("<Button-1>", lambda x: entry_invesment.delete(0, "end"))
entry_years.bind("<Button-1>", lambda x: entry_years.delete(0, "end"))

# create empthy text
text_incomeSMA = canvas.create_text(275, 348, text="", font=("Helvetica", 20), fill="black", anchor="n")
text_profitSMA = canvas.create_text(275, 383, text="", font=("Helvetica", 20), fill="black", anchor="n")
text_perProfitSMA = canvas.create_text(280, 418, text="", font=("Helvetica", 20), fill="black", anchor="n")

text_incomeRSI = canvas.create_text(675, 348, text="", font=("Helvetica", 20), fill="black", anchor="n")
text_profitRSI = canvas.create_text(675, 384, text="", font=("Helvetica", 20), fill="black", anchor="n")
text_perProfitRSI = canvas.create_text(680, 419, text="", font=("Helvetica", 20), fill="black", anchor="n")

# profit empthy text comparison
text_profit3 = canvas.create_text(630, 120, text="", font=("Helvetica", 20), fill="black", anchor="n")
text_profit4 = canvas.create_text(630, 145, text="", font=("Helvetica", 20), fill="black", anchor="n")

# create button
button_calculate = Button(root, text="คำนวณผลตอบแทน", highlightbackground="#adebd8",
                          bg="#3DDDCE", height=50, font=("Helvetica", 16), command=calculateProfit)
button_calculate = canvas.create_window(630, 20, anchor="n", window=button_calculate)

root.mainloop()
