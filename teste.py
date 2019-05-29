# -*- coding: cp1252 -*-

import os
import pandas as pd
from csv import reader


#CODBDI
STOCK=2
CALL=78
PUT=82

MIN_VOLNEG = 100

def subtraiDatasInteger(data_inicio, data_fim):
   from datetime import datetime
   date_format = "%Y%m%d"
   a = datetime.strptime(str(data_inicio), date_format)
   b = datetime.strptime(str(data_fim), date_format)
   delta = b - a
   return delta.days # that's it

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
            if CODBDI==CALL and "PETR" in CODNEG and (NOMRES[0] == "PETR" and len(NOMRES) == 1) and subtraiDatasInteger(DATA, DATVEN) <= 5 :
                tabela_opcoes_compra+=[[DATA, CODNEG,PREULT,PREEXE, DATVEN, TOTNEG]]
            if CODBDI==PUT and "PETR" in CODNEG and (NOMRES[0] == "PETR" and len(NOMRES) == 1) and subtraiDatasInteger(DATA, DATVEN) <= 5 :
                tabela_opcoes_venda+=[[DATA, CODNEG,PREULT,PREEXE, DATVEN, TOTNEG]]

print("qtd_compra=", len(tabela_opcoes_compra), ", qtd_venda=", len(tabela_opcoes_venda) )
df_acoes=pd.DataFrame(tabela_acoes, columns=['DATA', 'CODNEG','PREULT','PREEXE', 'DATVEN'])
df_op_compra=pd.DataFrame(tabela_opcoes_compra, columns=['DATA', 'CODNEG','PREULT','PREEXE', 'DATVEN', 'TOTNEG'])
df_op_venda=pd.DataFrame(tabela_opcoes_venda, columns=['DATA', 'CODNEG','PREULT','PREEXE', 'DATVEN', 'TOTNEG'])

MARGEM_MONEY = 0.20  # Diferença de até 10% será ATM
QTD_OPCOES = 10  # Compro apenas as N opções
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
   
   df_compra =  df_compra_ATM
   df_venda = df_venda_ATM
   
   dias += 1
   if( dias >= QTD_DIAS ):
      dias = 0
      print("Vendendo as opções do dia anterior")
      lista_po = [] #Opcoes que não aparecem como possíveis de venda
      for c in carteira_compra:
         if df_hoje_compra.loc[df_hoje_compra['CODNEG'] == c['CODNEG'] ].empty:
            print( "Opção de compra ", c['CODNEG'] ," virou Pó! Valor perdido=", c['INV'] )
            lista_po.append( c )
            saldo += (0-c['PREULT']) * c['QTD'] # Apuro lucro ou prejuízo
         else:
            preco_venda = float(df_hoje_compra.loc[df_hoje_compra['CODNEG'] == c['CODNEG'] ].PREULT) #Por quanto vendeu
            print("Vendi opção ", c['CODNEG'], ", comprei por ", c['PREULT'], ", vendi por ", preco_venda )
            saldo += (preco_venda-c['PREULT']) * c['QTD'] # Apuro lucro ou prejuízo
      #carteira_compra = lista_po
      carteira_compra = []
      
      lista_po = [] #Opcoes que não aparecem como possíveis de venda
      for v in carteira_venda:
         if df_hoje_venda.loc[df_hoje_venda['CODNEG'] == v['CODNEG'] ].empty:
            print( "Opção de venda ", v['CODNEG'] ," virou Pó! Valor perdido=", v['INV'] )
            lista_po.append( v )
            saldo += (0-v['PREULT']) * v['QTD'] # Apuro lucro ou prejuízo
         else:
            preco_venda = float(df_hoje_venda.loc[df_hoje_venda['CODNEG'] == v['CODNEG'] ].PREULT) #Por quanto vendeu
            print("Vendi opção ", v['CODNEG'], ", comprei por ", v['PREULT'], ", vendi por ", preco_venda )
            saldo += (preco_venda-v['PREULT']) * v['QTD'] # Apuro lucro ou prejuízo
      #carteira_venda = lista_po
      carteira_venda = []
         
      # Supondo que comprarei opcao de compra OTM e venda OTM, todo dia. Sempre o valor mais extremo.
      for nome_opcao in df_compra.head(QTD_OPCOES).CODNEG:
         quota_compra = int( saldo/(2*QTD_OPCOES) )
         preco_opcao = float(df_compra.loc[df_compra['CODNEG'] == nome_opcao].PREULT)
         qtd_compra = quota_compra/preco_opcao #int(quota_compra/preco_opcao)
         investido = int(qtd_compra*preco_opcao)
         strike = float(df_compra.loc[df_compra['CODNEG'] == nome_opcao].PREEXE)
         dt_vencimento = int(df_compra.loc[df_compra['CODNEG'] == nome_opcao].DATVEN)
         print("Comprarei Opção de compra ", nome_opcao, ", ao preço de ", preco_opcao, ", quantidade de ", qtd_compra, ", strike=", strike, ", vencimento=", dt_vencimento)
         ordem_compra = {'CODNEG' : nome_opcao, 'PREULT' : preco_opcao, 'QTD' : qtd_compra, 'INV' : investido, }
         carteira_compra.append( ordem_compra )
      
      for nome_opcao in df_venda.head(QTD_OPCOES).CODNEG:
         quota_compra = int( saldo/(2*QTD_OPCOES) )
         preco_opcao = float(df_venda.loc[df_venda['CODNEG'] == nome_opcao].PREULT)
         qtd_compra = quota_compra/preco_opcao #int(quota_compra/preco_opcao)
         investido = int(qtd_compra*preco_opcao)
         strike = float(df_venda.loc[df_venda['CODNEG'] == nome_opcao].PREEXE)
         dt_vencimento = int(df_compra.loc[df_compra['CODNEG'] == nome_opcao].DATVEN)
         print("Comprarei Opção de venda ", nome_opcao, ", ao preço de ", preco_opcao, ", quantidade de ", qtd_compra, ", strike=", strike, ", vencimento=", dt_vencimento)
         ordem_compra = {'CODNEG' : nome_opcao, 'PREULT' : preco_opcao, 'QTD' : qtd_compra, 'INV' : qtd_compra*preco_opcao, }
         carteira_venda.append( ordem_compra )
   
   print("Hoje eh", dia, ", spot=", spot, ", saldo final=", saldo)