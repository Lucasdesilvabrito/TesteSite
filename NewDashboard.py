# =========================================================
# IMPORTAÇÕES
# =========================================================

from dash import Dash, dcc, html
import plotly.express as px
import pandas as pd
import import_ipynb
from Abstracao_dados import df

# =========================================================
# CÓPIA DO DATAFRAME
# =========================================================

df = df.copy()

# =========================================================
# CONVERSÃO DE TEMPO PARA MINUTOS NUMÉRICOS
# =========================================================

df['duracao_minutos'] = (
    pd.to_timedelta(df['duracao_minutos_individual'])
    .dt.total_seconds() / 60
)

df['duracao_minutos_total'] = (
    pd.to_timedelta(df['duracao_minutos_total_por_ticket'])
    .dt.total_seconds() / 60
)

# =========================================================
# TRATAMENTO DE DATA
# =========================================================

df['data_atualizacao'] = pd.to_datetime(
    df['data_atualizacao'],
    errors='coerce'
)

# =========================================================
# PERÍODO DOS DADOS
# =========================================================

data_inicio = (
    df['data_atualizacao']
    .min()
    .strftime('%d/%m/%Y')
)

data_fim = (
    df['data_atualizacao']
    .max()
    .strftime('%d/%m/%Y')
)

dias_analisados = (
    df['data_atualizacao'].max()
    -
    df['data_atualizacao'].min()
).days

# =========================================================
# KPI'S
# =========================================================

total_tickets = df['id_ticket'].nunique()

tempo_medio = round(
    df['duracao_minutos_total'].mean(),
    2
)

problema_cti = round(
    (
        df['problema_nosso']
        .astype(str)
        .str.lower()
        .str.contains('sim', na=False)
        .mean()
    ) * 100,
    2
)

total_servicos = df['servico'].nunique()

ticket_mais_comum = (
    df['categoria']
    .dropna()
    .value_counts()
    .idxmax()
)

# =========================================================
# GRÁFICO 1 - PROBLEMA NOSSO
# =========================================================

fig_problema = px.pie(
    df,
    names='problema_nosso',
    hole=0.5
)

fig_problema.update_traces(
    marker=dict(
        colors=['#003366', '#28a745', '#ff9900']
    )
)

fig_problema.update_layout(
    paper_bgcolor='white',
    plot_bgcolor='white',
    margin=dict(l=10, r=10, t=30, b=10)
)

# =========================================================
# GRÁFICO 2 - TIPOS DE TICKET
# =========================================================

categoria_count = (
    df['categoria']
    .value_counts()
    .reset_index()
)

categoria_count.columns = [
    'categoria',
    'quantidade'
]

fig_categoria = px.bar(
    categoria_count,
    x='quantidade',
    y='categoria',
    orientation='h',
    text='quantidade'
)

fig_categoria.update_traces(
    marker_color='#003366'
)

fig_categoria.update_layout(
    xaxis_title='Quantidade',
    yaxis_title='Categoria',
    paper_bgcolor='white',
    plot_bgcolor='white',
    yaxis=dict(
        categoryorder='total ascending'
    )
)

# =========================================================
# GRÁFICO 3 - TEMPO MÉDIO POR MEIO
# =========================================================

tempo_por_meio = (
    df.groupby('meio')['duracao_minutos']
    .mean()
    .reset_index()
    .sort_values(
        by='duracao_minutos',
        ascending=False
    )
)

fig_tempo_meio = px.bar(
    tempo_por_meio,
    x='meio',
    y='duracao_minutos',
    text_auto='.2f'
)

fig_tempo_meio.update_traces(
    marker_color='#28a745'
)

fig_tempo_meio.update_layout(
    xaxis_title='Meio',
    yaxis_title='Tempo Médio (Min)',
    paper_bgcolor='white',
    plot_bgcolor='white'
)

# =========================================================
# GRÁFICO 4 - MÉDIA DE TEMPO MENSAL
# =========================================================

df['mes'] = (
    df['data_atualizacao']
    .dt.strftime('%Y-%m')
)

tempo_mensal = (
    df.groupby('mes')['duracao_minutos']
    .mean()
    .reset_index()
)

fig_tempo_mensal = px.line(
    tempo_mensal,
    x='mes',
    y='duracao_minutos',
    markers=True
)

fig_tempo_mensal.update_traces(
    line_color='#003366',
    marker_color='#28a745'
)

fig_tempo_mensal.update_layout(
    xaxis_title='Mês',
    yaxis_title='Tempo Médio (Min)',
    paper_bgcolor='white',
    plot_bgcolor='white'
)

# =========================================================
# GRÁFICO 5 - TOP SERVIÇOS
# =========================================================

top_servicos = (
    df['servico']
    .value_counts()
    .head(10)
    .reset_index()
)

top_servicos.columns = [
    'servico',
    'quantidade'
]

fig_servicos = px.bar(
    top_servicos,
    x='quantidade',
    y='servico',
    orientation='h',
    text='quantidade'
)

fig_servicos.update_traces(
    marker_color='#003366'
)

fig_servicos.update_layout(
    xaxis_title='Quantidade',
    yaxis_title='Serviço',
    paper_bgcolor='white',
    plot_bgcolor='white',
    yaxis=dict(
        categoryorder='total ascending'
    )
)

# =========================================================
# GRÁFICO 6 - SLA / CLASSIFICAÇÃO
# =========================================================

fig_classificacao = px.box(
    df,
    x='classificacao',
    y='duracao_minutos',
    color='classificacao'
)

fig_classificacao.update_layout(
    xaxis_title='Classificação',
    yaxis_title='Tempo (Min)',
    paper_bgcolor='white',
    plot_bgcolor='white',
    showlegend=False
)

# =========================================================
# MATRIZ DE ESPECIALISTAS E EQUIPES
# =========================================================

especialistas = (

    df.groupby(['servico', 'consultor'])

    .agg({
        'id_ticket': 'nunique',
        'duracao_minutos': 'mean'
    })

    .reset_index()
)

especialistas.columns = [
    'servico',
    'consultor',
    'tickets_resolvidos',
    'tempo_medio'
]

especialistas = especialistas.dropna(
    subset=['consultor', 'servico']
)

# =========================================================
# NÍVEL TÉCNICO
# =========================================================

def nivel_tecnico(qtd):

    if qtd >= 1000:
        return 'Especialista'

    elif qtd >= 600:
        return 'Sênior'

    elif qtd >= 250:
        return 'Pleno'

    return 'Júnior'


especialistas['nivel'] = (
    especialistas['tickets_resolvidos']
    .apply(nivel_tecnico)
)

# =========================================================
# DEFINIÇÃO DAS EQUIPES
# =========================================================

lideres = {
    'Janaina': 'Equipe Alpha',
    'Márcio Takeshi': 'Equipe Omega'
}

def definir_equipe(row):

    consultor = row['consultor']

    if consultor in lideres:
        return lideres[consultor]

    if row['nivel'] == 'Especialista':
        return 'Equipe Estratégica'

    if row['nivel'] == 'Sênior':
        return 'Equipe Avançada'

    if row['nivel'] == 'Pleno':
        return 'Equipe Operacional'

    return 'Equipe Formação'


especialistas['equipe'] = especialistas.apply(
    definir_equipe,
    axis=1
)

# =========================================================
# PRIORIZAÇÃO DOS SERVIÇOS MAIS RELEVANTES
# =========================================================

servicos_relevantes = (
    df['servico']
    .value_counts()
    .head(12)
    .index
)

especialistas = especialistas[
    especialistas['servico'].isin(servicos_relevantes)
]

# =========================================================
# ESTILOS
# =========================================================

BACKGROUND = '#f2f2f2'
PRIMARY = '#003366'
SECONDARY = '#28a745'

CARD_STYLE = {
    'backgroundColor': 'white',
    'padding': '15px',
    'borderRadius': '10px',
    'boxShadow': '0px 2px 6px rgba(0,0,0,0.1)',
    'margin': '10px',
    'flex': '1',
    'minWidth': '350px'
}

KPI_STYLE = {
    'backgroundColor': 'white',
    'padding': '20px',
    'borderRadius': '10px',
    'textAlign': 'center',
    'boxShadow': '0px 2px 6px rgba(0,0,0,0.1)',
    'flex': '1',
    'margin': '10px',
    'borderTop': f'5px solid {SECONDARY}',
    'minWidth': '220px'
}

TITLE_STYLE = {
    'fontSize': '18px',
    'fontWeight': 'bold',
    'marginBottom': '10px',
    'color': PRIMARY,
    'fontFamily': 'Arial'
}

# =========================================================
# COMPONENTE VISUAL
# =========================================================

painel_especialistas = []

for servico in servicos_relevantes:

    equipe = especialistas[
        especialistas['servico'] == servico
    ].sort_values(
        by='tickets_resolvidos',
        ascending=False
    )

    if equipe.empty:
        continue

    cards_operadores = []

    for _, row in equipe.iterrows():

        largura = min(
            (row['tickets_resolvidos'] / 1200) * 100,
            100
        )

        if row['nivel'] == 'Especialista':
            cor = '#003366'

        elif row['nivel'] == 'Sênior':
            cor = '#0055aa'

        elif row['nivel'] == 'Pleno':
            cor = '#28a745'

        else:
            cor = '#ff9900'

        cards_operadores.append(

            html.Div(

                style={
                    'marginBottom': '22px',
                    'paddingBottom': '10px',
                    'borderBottom': '1px solid #eeeeee'
                },

                children=[

                    html.Div(

                        style={
                            'display': 'flex',
                            'justifyContent': 'space-between',
                            'marginBottom': '6px'
                        },

                        children=[

                            html.Div([

                                html.Strong(
                                    row['consultor'],
                                    style={
                                        'color': PRIMARY,
                                        'fontSize': '16px'
                                    }
                                ),

                                html.Div(
                                    row['equipe'],
                                    style={
                                        'fontSize': '12px',
                                        'color': '#777'
                                    }
                                )
                            ]),

                            html.Span(
                                row['nivel'],
                                style={
                                    'color': cor,
                                    'fontWeight': 'bold',
                                    'fontSize': '14px'
                                }
                            )
                        ]
                    ),

                    html.Div(

                        style={
                            'width': '100%',
                            'height': '13px',
                            'backgroundColor': '#e6e6e6',
                            'borderRadius': '20px',
                            'overflow': 'hidden'
                        },

                        children=[

                            html.Div(

                                style={
                                    'width': f'{largura}%',
                                    'height': '100%',
                                    'backgroundColor': cor,
                                    'borderRadius': '20px',
                                    'transition': '0.4s'
                                }
                            )
                        ]
                    ),

                    html.Div(

                        style={
                            'display': 'flex',
                            'justifyContent': 'space-between',
                            'fontSize': '13px',
                            'marginTop': '6px',
                            'color': '#666'
                        },

                        children=[

                            html.Span(
                                f"{row['tickets_resolvidos']} tickets"
                            ),

                            html.Span(
                                f"{row['tempo_medio']:.1f} min méd."
                            )
                        ]
                    )
                ]
            )
        )

    painel_especialistas.append(

        html.Div(

            style={
                **CARD_STYLE,
                'minWidth': '460px'
            },

            children=[

                html.Div(
                    f'Equipe Recomendada - {servico}',
                    style=TITLE_STYLE
                ),

                html.Div(

                    style={
                        'marginBottom': '15px',
                        'padding': '10px',
                        'backgroundColor': '#f8f9fa',
                        'borderRadius': '8px',
                        'fontSize': '13px',
                        'color': '#444'
                    },

                    children=[

                        html.Div("🔵 Especialista → domina o serviço e resolve alto volume"),
                        html.Div("🟦 Sênior → experiência elevada e suporte avançado"),
                        html.Div("🟢 Pleno → operação estável e produtividade consistente"),
                        html.Div("🟠 Júnior → em desenvolvimento técnico")
                    ]
                ),

                *cards_operadores
            ]
        )
    )

# =========================================================
# APP
# =========================================================

app = Dash(__name__)

# =========================================================
# LAYOUT
# =========================================================

app.layout = html.Div(

    style={
        'backgroundColor': BACKGROUND,
        'padding': '20px',
        'fontFamily': 'Arial'
    },

    children=[

        # HEADER
        html.Div(
            children='Dashboard Empresarial - CTI',

            style={
                'backgroundColor': PRIMARY,
                'color': 'white',
                'padding': '20px',
                'borderRadius': '10px',
                'fontSize': '28px',
                'fontWeight': 'bold',
                'textAlign': 'center',
                'marginBottom': '20px'
            }
        ),

        # PERÍODO
        html.Div(

            children=[
                html.H3(
                    f'Dados analisados de {data_inicio} até {data_fim} | {dias_analisados} dias analisados'
                )
            ],

            style={
                'background': 'linear-gradient(to right, #003366, #0055aa)',
                'padding': '12px',
                'borderRadius': '10px',
                'marginBottom': '20px',
                'textAlign': 'center',
                'color': 'white',
                'fontWeight': 'bold',
                'fontSize': '18px',
                'boxShadow': '0px 2px 6px rgba(0,0,0,0.2)'
            }
        ),

        # KPI'S
        html.Div(

            style={
                'display': 'flex',
                'flexWrap': 'wrap'
            },

            children=[

                html.Div(style=KPI_STYLE, children=[
                    html.H3('🎫 Total Tickets'),
                    html.H1(total_tickets)
                ]),

                html.Div(style=KPI_STYLE, children=[
                    html.H3('⏱ Tempo Médio'),
                    html.H1(f'{tempo_medio:.2f} min')
                ]),

                html.Div(style=KPI_STYLE, children=[
                    html.H3('⚠ Problema CTI'),
                    html.H1(f'{problema_cti}%')
                ]),

                html.Div(style=KPI_STYLE, children=[
                    html.H3('🛠 Serviços'),
                    html.H1(total_servicos)
                ]),

                html.Div(style=KPI_STYLE, children=[
                    html.H3('📌 Ticket Mais Comum'),
                    html.H1(ticket_mais_comum)
                ]),
            ]
        ),

        # PRIMEIRA LINHA
        html.Div(

            style={
                'display': 'flex',
                'flexWrap': 'wrap'
            },

            children=[

                html.Div(style=CARD_STYLE, children=[
                    html.Div(
                        "Problema Nosso x Não Nosso",
                        style=TITLE_STYLE
                    ),
                    dcc.Graph(figure=fig_problema)
                ]),

                html.Div(style=CARD_STYLE, children=[
                    html.Div(
                        "Tipos de Ticket",
                        style=TITLE_STYLE
                    ),
                    dcc.Graph(figure=fig_categoria)
                ]),

                html.Div(style=CARD_STYLE, children=[
                    html.Div(
                        "Tempo Médio Mensal",
                        style=TITLE_STYLE
                    ),
                    dcc.Graph(figure=fig_tempo_mensal)
                ])
            ]
        ),

        # SEGUNDA LINHA
        html.Div(

            style={
                'display': 'flex',
                'flexWrap': 'wrap'
            },

            children=[

                html.Div(style=CARD_STYLE, children=[
                    html.Div(
                        "Tempo Médio por Meio",
                        style=TITLE_STYLE
                    ),
                    dcc.Graph(figure=fig_tempo_meio)
                ]),

                html.Div(style=CARD_STYLE, children=[
                    html.Div(
                        "Top 10 Serviços",
                        style=TITLE_STYLE
                    ),
                    dcc.Graph(figure=fig_servicos)
                ]),

                html.Div(style=CARD_STYLE, children=[
                    html.Div(
                        "SLA / Tempo por Classificação",
                        style=TITLE_STYLE
                    ),
                    dcc.Graph(figure=fig_classificacao)
                ])
            ]
        ),

        # MATRIZ DE ESPECIALISTAS
        html.Div(

            style={
                'display': 'flex',
                'flexWrap': 'wrap'
            },

            children=painel_especialistas
        )
    ]
)

# =========================================================
# EXECUÇÃO
# =========================================================

if __name__ == '__main__':

    app.run(
        debug=True,
        port=8050
    )