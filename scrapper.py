#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import sys
import os
import json
from bs4 import BeautifulSoup as bs
from xml.etree import ElementTree as et

def validar_url(url):
    url = url.strip()

    if not 'http://' in url and not 'https://' in url:
        url = 'http://' + url

    return url

def obter_pagina():
    try:
        if len(sys.argv) > 1:
            url = sys.argv[1]
        else:
            url = input('Insira a URL da página Web: ')

        pagina = requests.get(validar_url(url))
        print('URL: {url}'.format(url=pagina.url))
        return pagina
    except:
        print('A URL {} não pode ser aberta. Verifique-a.'.format(url))
        print('{}: {}'.format(sys.exc_info()[0], sys.exc_info()[1]))
        exit()


def preparar_gravacao(nome_arquivo):
    diretorio = 'relatorios/'

    if not os.path.exists(diretorio):
        os.makedirs(diretorio)

    remocao = (('http://', ''), ('https://', ''), ('www.', ''), ('.htm', ''),
               ('.html', ''), ('.asp', ''), ('.php', ''), ('/', '_'))

    for item in remocao:
        nome_arquivo = nome_arquivo.replace(item[0], item[1])

    if nome_arquivo.endswith('_'):
        nome_arquivo = nome_arquivo[:len(nome_arquivo) - 1]


    return diretorio + nome_arquivo


def gerar_xml_parcial(arquivo, url, titulo, elementos, extensao='.xml'):
    raiz = et.Element('relatorio')  # create the element first
    tree = et.ElementTree(raiz)

    node = et.Element('URL')
    node.text = url
    raiz.append(node)

    node = et.Element('titulo')
    node.text = titulo
    raiz.append(node)

    node = et.Element('elementos')

    for key in sorted(elementos):
        field = et.Element(key)
        field.text = str(elementos[key])
        node.append(field)

    raiz.append(node)

    try:
        with open(arquivo + extensao, 'w', encoding='utf-8') as file:
            tree.write(file, xml_declaration=True, encoding='unicode')

        print('Resumo de elementos em formato XML criado no arquivo texto criado no arquivo:', arquivo + extensao)
    except:
        print('Erro na criação do relatório XML', arquivo + extensao)


def gerar_txt_parcial(arquivo, url, titulo, elementos, extensao='.txt'):

    try:
        relatorio = open(arquivo + extensao, 'wt')
    except:
        print('Erro na abertura do arquivo ' + arquivo + extensao)
        exit()

    relatorio.write('-- Relatório -- \n')
    relatorio.write('Endereço (URL): %s\n' % url)
    relatorio.write('Título: %s\n' % titulo)
    relatorio.write('\n-- Elementos --\n')

    elementos_nome = {'botoes': 'Botões', 'imagens': 'Imagens', 'cabecalhos': 'Cabeçalhos',
                      'links': 'Links', 'textos': 'Caixas de texto', 'selects': 'Listas de seleção/combinação',
                      'tabelas': 'Tabelas'}

    for key in sorted(elementos):
        relatorio.write('%s: %s\n' % (elementos_nome[key], elementos[key]))

    print('Resumo de elementos em formato TXT criado no arquivo:', arquivo + extensao)

    relatorio.close()


def analisar_elementos(soup):
    elementos = {'botoes': 0, 'imagens': 0, 'cabecalhos': 0, 'links': 0, 'textos': 0, 'selects': 0,
                 'tabelas': 0}

    # Botões
    elementos['botoes'] += len(soup.find_all('button'))
    elementos['botoes'] += sum(1 if e.get('type') in ['button', 'submit', 'reset'] else 0 for e in soup.find_all('input'))

    # Imagens
    elementos['imagens'] += len(soup.find_all('img'))
    elementos['imagens'] += sum(1 if e.get('type') == 'image' else 0 for e in soup.find_all('input'))

    # Cabeçalhos
    for x in range(6):
        elementos['cabecalhos'] += len(soup.find_all('h%d' % (x + 1)))

    # Links
    elementos['links'] += sum(1 if e.get('href') else 0 for e in soup.find_all('a'))

    # Inputs
    elementos['textos'] += len(soup.find_all('textarea'))
    elementos['textos'] += sum(1 if e.get('type') in ['text', 'email', 'password'] else 0 for e in soup.find_all('input'))

    # Selects
    elementos['selects'] += len(soup.find_all('select'))

    # Tabelas
    elementos['tabelas'] += len(soup.find_all('table'))

    return elementos


def gerar_questionario(arquivo, url, titulo, elementos):

    fquestoes = open('base_questoes.json')
    questoes = json.loads(fquestoes.read())

    extensao = '.txt'

    arquivo += '_QUEST'
    try:
        questionario = open(arquivo + extensao, 'w')
    except:
        print('Erro na criação do questionário', relatorio)
        exit()

    for q in questoes:
        for key in elementos:
            if (elementos[key] > 0):
                if key in q['Tipo']:
                    q['Submeter'] = True

    ordem = 0

    elementos_nome = {'botoes': 'Botões', 'imagens': 'Imagens', 'cabecalhos': 'Cabeçalhos',
                      'links': 'Links', 'textos': 'Caixas de texto', 'selects': 'Listas de seleção/combinação',
                      'tabelas': 'Tabelas'}

    qtd_questoes = 0

    for q in questoes:
        if q['Submeter']:
            qtd_questoes += 1

    questionario.write('--- Questionário de usabilidade e ergonomia ---\n\n')
    questionario.write('Endereço (URL): %s\n' % url)
    questionario.write('Título da página: %s\n' % titulo)
    questionario.write('\nQuantificação de elementos:\n\n')

    for key in sorted(elementos):
        questionario.write('%s: %s\n' % (elementos_nome[key], elementos[key]))

    questionario.write('\n--Início do Questionário --\n\n')

    for q in questoes:
        if q['Submeter']:
            ordem += 1
            questionario.write('- Questão %03d de %03d - \n\nCritério: %s.\nAplica-se a: ' %
                               (ordem, qtd_questoes, q['Critério']))

            aplicaveis = []

            if 'janela' in q['Descrição']:
                questionario.write('Janela, ')

            for tipo in q['Tipo']:
                if elementos[tipo] > 0:
                    aplicaveis.append(tipo)

            cont = 0

            for tipo in aplicaveis:
                if elementos[tipo] > 0:

                    if len(aplicaveis) == 1:
                        questionario.write(elementos_nome[tipo] + '.\n')
                    elif cont == (len(aplicaveis) - 1):
                        questionario.write(' e ' + elementos_nome[tipo] + '.\n')
                    elif cont == (len(aplicaveis) - 2):
                        questionario.write(elementos_nome[tipo])
                    else:
                        questionario.write(elementos_nome[tipo] + ', ')

                    cont += 1

            questionario.write('\n' + q['Descrição'] + '\n')
            questionario.write('[_] Sim\n')
            questionario.write('[_] Não\n')
            questionario.write('[_] Não Aplicável\n\n')


    questionario.close()
    print('Questionário disponível em', arquivo + extensao)


# início
print('-- Gerador de Questionário de Usabilidade -- \n')

pagina = obter_pagina()
soup = bs(pagina.text, 'html.parser')
elementos = analisar_elementos(soup)
arquivo = preparar_gravacao(pagina.url)
gerar_txt_parcial(arquivo, pagina.url, soup.title.string, elementos)
gerar_xml_parcial(arquivo, pagina.url, soup.title.string, elementos)
gerar_questionario(arquivo, pagina.url, soup.title.string, elementos)