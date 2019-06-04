# -*- coding: cp1252 -*-

import os
import pandas as pd
from csv import reader


#CODBDI
STOCK=2
CALL=78
PUT=82

MIN_VOLNEG = 0
MAX_DIAS_OPCAO = 3

def subtraiDatasInteger(data_inicio, data_fim):
   from datetime import datetime
   date_format = "%Y%m%d"
   a = datetime.strptime(str(data_inicio), date_format)
   b = datetime.strptime(str(data_fim), date_format)
   delta = b - a
   return delta.days # that's it

def estimaFatorDeDesconto(call, put, strike, spot):
   fatorDeDesconto = ((put + spot)-call)/strike
   return fatorDeDesconto

def estimaVariacaoPrecos(strike, spot, fatorDesconto):
   varia = spot - fatorDesconto*strike
   return varia

def estimaPrecoOpcaoVenda(strike, spot, fatorDeDesconto, precoCompra):
   pv = precoCompra + precoCompra*strike - spot
   return pv
   
selic = pd.read_csv('Selic.csv', delimiter=';') #, columns=['DATA', 'SELIC'] )
   
def s(a,i,f): return a[i-1:f].strip()
def f(a,i,f): return float(a[i-1:f])/100
def i(a,i,f): return int(a[i-1:f])

tabela_acoes=[]
tabela_opcoes_compra=[]
tabela_opcoes_venda=[]
for arquivo in os.listdir('./input')[:1]:    
    with open('./input/'+arquivo,'r') as arquivo_txt:
        for linha in reader(arquivo_txt):
            linha=linha[0]

            TIPREG=i(linha,1,2)
            if TIPREG==0 or TIPREG==99: continue;
            
            DATA=i(linha,3,10)
            CODBDI=i(linha,11,12)
            CODNEG=s(linha,13,24)
            TPMERC=s(linha,25,27)
            NOMRES=s(linha,28,39).split()
            ESPECI=s(linha,40,49).strip()
            PREABE=f(linha,57,69)
            PREMAX=f(linha,70,82)
            PREMIN=f(linha,83,95)
            PREMED=f(linha,96,108)
            PREULT=f(linha,109,121)
            TOTNEG=i(linha,148,152)
            QUATOT=i(linha,153,170)
            VOLTOT=f(linha,171,188)
            PREEXE=f(linha,189,201)
            INDOPC=i(linha,202,202)
            DATVEN=i(linha,203,210)
            FATCOT=i(linha,211,217)

            #Se for uma opção de compra lista a data, o código de negociação, o preço de exercicio e data de vencimento
            if CODBDI==STOCK and "PETR4" in CODNEG:
                tabela_acoes+=[[DATA, CODNEG,PREULT,PREEXE, DATVEN]] 
            if CODBDI==CALL and "PETR" in CODNEG and (NOMRES[0] == "PETR" and len(NOMRES) == 1) and subtraiDatasInteger(DATA, DATVEN) <= MAX_DIAS_OPCAO :
                tabela_opcoes_compra+=[[DATA, CODNEG,PREULT,PREEXE, DATVEN, TOTNEG]]
            if CODBDI==PUT and "PETR" in CODNEG and (NOMRES[0] == "PETR" and len(NOMRES) == 1) and subtraiDatasInteger(DATA, DATVEN) <= MAX_DIAS_OPCAO :
                tabela_opcoes_venda+=[[DATA, CODNEG,PREULT,PREEXE, DATVEN, TOTNEG]]

print("qtd_compra=", len(tabela_opcoes_compra), ", qtd_venda=", len(tabela_opcoes_venda) )
df_acoes=pd.DataFrame(tabela_acoes, columns=['DATA', 'CODNEG','PREULT','PREEXE', 'DATVEN'])
df_op_compra=pd.DataFrame(tabela_opcoes_compra, columns=['DATA', 'CODNEG','PREULT','PREEXE', 'DATVEN', 'TOTNEG'])
df_op_venda=pd.DataFrame(tabela_opcoes_venda, columns=['DATA', 'CODNEG','PREULT','PREEXE', 'DATVEN', 'TOTNEG'])

MARGEM_MONEY = 0.20  # Diferença de até 10% será ATM
QTD_OPCOES = 3  # Compro apenas as N opções
QTD_DIAS = 1 # A cada tempo      

saldo = 1000.0
carteira_compra = [] #Opcoes de compra que tem na carteira
carteira_venda = [] #Opcoes de venda que tem na carteira
dias = 0

for dia in df_acoes.DATA:
   spot = float(df_acoes.loc[df_acoes['DATA'] == dia].PREULT)
   df_hoje_compra = df_op_compra.loc[df_op_compra['DATA'] == dia]
   df_compra_ITM = df_hoje_compra.loc[ spot - df_hoje_compra['PREEXE'] > MARGEM_MONEY ].sort_values(by=['PREEXE', 'DATVEN'], ascending=[True, False])
   df_compra_OTM = df_hoje_compra.loc[ spot - df_hoje_compra['PREEXE'] < -1*MARGEM_MONEY ].sort_values(by=['PREEXE', 'DATVEN'], ascending=[False, False])
   df_compra_ATM = df_hoje_compra.loc[ (spot - df_hoje_compra['PREEXE'] >= -1*MARGEM_MONEY) & (spot - df_hoje_compra['PREEXE'] <= MARGEM_MONEY) ].sort_values(by=['PREEXE', 'DATVEN'], ascending=[True, False])
   
   df_hoje_venda = df_op_venda.loc[df_op_venda['DATA'] == dia]
   df_venda_OTM = df_hoje_venda.loc[ spot - df_hoje_venda['PREEXE'] > MARGEM_MONEY ].sort_values(by=['PREEXE', 'DATVEN'], ascending=[True, False])
   df_venda_ITM = df_hoje_venda.loc[ spot - df_hoje_venda['PREEXE'] < -1*MARGEM_MONEY ].sort_values(by=['PREEXE', 'DATVEN'], ascending=[False, False])
   df_venda_ATM = df_hoje_venda.loc[ (spot - df_hoje_venda['PREEXE'] >= -1*MARGEM_MONEY) & (spot - df_hoje_venda['PREEXE'] <= MARGEM_MONEY) ].sort_values(by=['PREEXE', 'DATVEN'], ascending=[False, False])
   
   df_compra =  df_compra_OTM
   df_venda = df_venda_OTM
   
   dias += 1
   if( dias >= QTD_DIAS ):
      dias = 0
      print("Vendendo as opções do dia anterior")
      for c in carteira_compra:
         fatorDesconto = float(selic.loc[selic['data'] == dia].valor) # Busco na Selic
         fatorDesconto = 1 # Aproximação
         strike = c['PREEXE']
         varPre = estimaVariacaoPrecos(strike=strike, spot=spot, fatorDesconto=fatorDesconto)
         print("Preço alterando, ", varPre, " da Opção de compra ", c['CODNEG'], " e correspondente opção de venda ", )
         saldo += varPre * c['QTD']
      carteira_compra = []
                  
      for nome_opcao in df_compra.head(QTD_OPCOES).CODNEG:
         quota_compra = int( saldo/(2*QTD_OPCOES) )
         preco_opcao = float(df_compra.loc[df_compra['CODNEG'] == nome_opcao].PREULT)
         qtd_compra = quota_compra/preco_opcao #int(quota_compra/preco_opcao)
         investido = int(qtd_compra*preco_opcao)
         strike = float(df_compra.loc[df_compra['CODNEG'] == nome_opcao].PREEXE)
         fatorDesconto = float(selic.loc[selic['data'] == dia].valor) # Busco na Selic
         fatorDesconto = 1 # Aproximação
         dt_vencimento = int(df_compra.loc[df_compra['CODNEG'] == nome_opcao].DATVEN)
         print("Comprarei Opção de compra ", nome_opcao, ", ao preço de ", preco_opcao, ", quantidade de ", qtd_compra, ", strike=", strike, ", vencimento=", dt_vencimento)
         ordem_compra = {'CODNEG' : nome_opcao, 'PREULT' : preco_opcao, 'QTD' : qtd_compra, 'INV' : investido, 'PREEXE' : strike }
         carteira_compra.append( ordem_compra )
         valoresMeses = {"A" : "M", "B" : "N", "C" : "O", "D" : "P", "E" : "Q", "F" : "R", "G" : "S", "H" : "T", "I" : "U", "J" : "V", "K" : "W", "L" : "X", }
         nomeOpVenda = nome_opcao[0:4] + valoresMeses[nome_opcao[4]] + nome_opcao[5:]
         preco_venda_c = estimaPrecoOpcaoVenda(strike=strike, spot=spot, fatorDeDesconto=fatorDesconto, precoCompra=preco_opcao)
         qtd_compra_v = quota_compra/preco_venda_c #int(quota_compra/preco_opcao)
         #strike_v = float(df_venda.loc[df_venda['CODNEG'] == nomeOpVenda].PREEXE)
         strike_v = strike  # Vai que não tem
         #dt_vencimento_v = int(df_venda.loc[df_venda['CODNEG'] == nomeOpVenda].DATVEN)
         dt_vencimento_v = dt_vencimento # Vai que não tem
         investido_v = int(qtd_compra_v*preco_venda_c)
         print("Comprarei Opção de venda ", nomeOpVenda, ", ao preço de ", preco_venda_c, ", quantidade de ", qtd_compra_v, ", strike=", strike_v, ", vencimento=", dt_vencimento_v)
         ordem_compra_v = {'CODNEG' : nomeOpVenda, 'PREULT' : preco_venda_c, 'QTD' : qtd_compra_v, 'INV' : investido_v, }
         carteira_venda.append( ordem_compra_v )
         
   print("Hoje eh", dia, ", spot=", spot, ", saldo final=", saldo)