"""
Plotly chart builders for the microgrid dashboard.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from settings import ALL_SCENARIOS, SCENARIO_LABELS
from components import colors


def plot_time_series(results, scenarios):
    """
    Interactive 5-panel time series for one or more scenarios (overlay).
    `scenarios` can be a single key or a list of keys.
    """
    if isinstance(scenarios, str):
        scenarios = [scenarios]

    fig = make_subplots(
        rows=5, cols=1, shared_xaxes=True,
        vertical_spacing=0.04,
        subplot_titles=('Renewable Generation', 'Battery Power',
                        'State of Charge', 'Grid Power', 'DC Bus Voltage'),
    )

    line_styles = ['solid', 'dash', 'dot', 'dashdot', 'longdash']
    color_map = dict(zip(ALL_SCENARIOS, colors()))

    for idx, sc_key in enumerate(scenarios):
        r = results[sc_key]
        t = np.arange(len(r.time_h)) / 24.0
        ls = line_styles[idx % len(line_styles)]
        color = color_map.get(sc_key, colors()[idx % len(colors())])
        label = SCENARIO_LABELS.get(sc_key, sc_key)

        if idx == 0:
            fig.add_trace(go.Scatter(x=t, y=r.p_pv, name=f'{label} PV',
                                     line=dict(color='#F28E2B')), row=1, col=1)
            fig.add_trace(go.Scatter(x=t, y=r.p_wind, name=f'{label} Wind',
                                     line=dict(color='#4E79A7')), row=1, col=1)
        else:
            fig.add_trace(go.Scatter(x=t, y=r.p_pv, name=f'{label} PV',
                                     line=dict(color='#F28E2B', dash=ls), opacity=0.5),
                          row=1, col=1)
            fig.add_trace(go.Scatter(x=t, y=r.p_wind, name=f'{label} Wind',
                                     line=dict(color='#4E79A7', dash=ls), opacity=0.5),
                          row=1, col=1)

        opacity = 0.6 if idx == 0 else 0.25
        bat_pos = np.where(r.p_bat >= 0, r.p_bat, 0)
        bat_neg = np.where(r.p_bat < 0, r.p_bat, 0)
        fig.add_trace(go.Bar(x=t, y=bat_pos, name=f'{label} Discharge',
                             marker_color='#E15759', opacity=opacity,
                             legendgroup=f'{sc_key}_bat'), row=2, col=1)
        fig.add_trace(go.Bar(x=t, y=bat_neg, name=f'{label} Charge',
                             marker_color='#59A14F', opacity=opacity,
                             legendgroup=f'{sc_key}_bat'), row=2, col=1)

        fig.add_trace(go.Scatter(x=t, y=r.soc * 100, name=f'{label} SOC',
                                 line=dict(color=color, dash=ls)), row=3, col=1)

        grid_pos = np.where(r.p_grid >= 0, r.p_grid, 0)
        grid_neg = np.where(r.p_grid < 0, r.p_grid, 0)
        fig.add_trace(go.Bar(x=t, y=grid_pos, name=f'{label} Import',
                             marker_color='#E15759', opacity=opacity,
                             legendgroup=f'{sc_key}_grid'), row=4, col=1)
        fig.add_trace(go.Bar(x=t, y=grid_neg, name=f'{label} Export',
                             marker_color='#4E79A7', opacity=opacity,
                             legendgroup=f'{sc_key}_grid'), row=4, col=1)

        fig.add_trace(go.Scatter(x=t, y=r.vdc, name=f'{label} Vdc',
                                 line=dict(color=color, dash=ls, width=0.8)), row=5, col=1)

    fig.add_hline(y=20, line_dash='dot', line_color='#E15759', row=3, col=1)
    fig.add_hline(y=90, line_dash='dot', line_color='#E15759', row=3, col=1)
    fig.add_hline(y=800, line_dash='dash', line_color='#E15759', row=5, col=1)

    title = 'Time Series — ' + ', '.join(SCENARIO_LABELS.get(s, s) for s in scenarios)
    fig.update_layout(height=800, title_text=title, hovermode='x unified',
                      showlegend=True,
                      legend=dict(font=dict(size=9)),
                      margin=dict(r=180))
    fig.update_xaxes(title_text='Time (days)', row=5, col=1)
    for r, yl in [(1, 'kW'), (2, 'kW'), (3, '%'), (4, 'kW'), (5, 'V')]:
        fig.update_yaxes(title_text=yl, row=r, col=1)
    return fig


def plot_kpi_comparison(kpi_table):
    """6-panel KPI bar chart comparing scenarios."""
    df = pd.DataFrame(kpi_table).T
    df.index = [SCENARIO_LABELS.get(k, k) for k in df.index]

    kpi_fields = {
        'VRI': 'VRI (%)', 'Cost': 'Total Cost ($)',
        'RE_Ratio': 'RE Ratio (%)', 'Peak_Red': 'Peak Reduction (%)',
        'Settle_Time': 'Settling Time (s)', 'Overshoot': 'Overshoot (%)',
    }
    available = [k for k in kpi_fields if k in df.columns]
    n = len(available)

    fig = make_subplots(rows=(n + 2) // 3, cols=3,
                        subplot_titles=[kpi_fields[k] for k in available])

    for i, k in enumerate(available):
        r, c = i // 3 + 1, i % 3 + 1
        pal = colors()[:len(df)]
        fig.add_trace(go.Bar(x=df.index, y=df[k], marker_color=pal,
                             text=df[k].round(1), textposition='outside'),
                      row=r, col=c)

    fig.update_layout(height=300 * ((n + 2) // 3), showlegend=False,
                      title_text='Scenario Comparison - Key Performance Indicators')
    return fig


def plot_cost_comparison(results):
    """Cost bar chart across scenarios."""
    names = [SCENARIO_LABELS.get(s, s) for s in results]
    costs = [float(np.sum(results[s].cost)) for s in results]
    pal = colors()[:len(results)]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=names, y=costs, marker_color=pal,
                         text=[f'${c:.0f}' for c in costs], textposition='outside'))
    fig.add_hline(y=0, line_color='#333', line_width=0.5)
    fig.update_layout(title='Economic Comparison Across Scenarios',
                      yaxis_title='Total Cost ($)', height=400)
    return fig


def plot_sensitivity(sens_results, param_name):
    """Interactive sensitivity line chart."""
    names = list(sens_results.keys())
    costs = [sens_results[n]['Cost'] for n in names]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=names, y=costs, mode='lines+markers',
                             line=dict(color='#E15759', width=2),
                             marker=dict(size=10), name='Total Cost'))
    fig.add_trace(go.Scatter(x=names,
                             y=[sens_results[n]['RE_Ratio'] for n in names],
                             mode='lines+markers',
                             line=dict(color='#59A14F', width=2, dash='dot'),
                             marker=dict(size=8), name='RE Ratio (%)', yaxis='y2'))

    fig.update_layout(title=f'Sensitivity: {param_name}',
                      xaxis_title=param_name, yaxis_title='Total Cost ($)',
                      yaxis2=dict(overlaying='y', side='right', title='RE Ratio (%)'),
                      hovermode='x unified', height=400)
    return fig


def plot_cost_accumulation(results):
    """Cumulative cost over time for S1, S3, S5."""
    fig = go.Figure()
    for key, color in [('S1', '#6C6C6C'), ('S3', '#59A14F'), ('S5', '#E15759')]:
        if key in results:
            cum = np.cumsum(results[key].cost)
            t = np.arange(len(cum)) / 24.0
            fig.add_trace(go.Scatter(x=t, y=cum, name=SCENARIO_LABELS.get(key, key),
                                     line=dict(color=color, width=2)))
    fig.update_layout(title='Cost Accumulation Over Time',
                      xaxis_title='Time (days)', yaxis_title='Cumulative Cost ($)',
                      hovermode='x unified', height=400)
    fig.add_hline(y=0, line_color='#333', line_width=0.5)
    return fig


def plot_mode_timeline(results):
    """PMS operating mode Gantt chart."""
    r = results
    modes = np.array(r.mode)
    t = np.arange(len(modes)) / 24.0

    mode_colors = ['#4E79A7', '#F28E2B', '#59A14F', '#E15759', '#B07AA1', '#8C564B']
    mode_labels = ['M1: Charge', 'M2: ValleyFill', 'M3: Export',
                   'M4: PeakClip', 'M5: Discharge', 'M6: Import']

    fig = go.Figure()
    for m in range(1, 7):
        mask = modes == m
        if not mask.any():
            continue
        seg_starts, seg_ends = [], []
        in_seg = False
        for i, m_val in enumerate(mask):
            if m_val and not in_seg:
                seg_starts.append(t[i])
                in_seg = True
            elif not m_val and in_seg:
                seg_ends.append(t[i])
                in_seg = False
        if in_seg:
            seg_ends.append(t[-1])

        for start, end in zip(seg_starts, seg_ends):
            fig.add_trace(go.Scatter(
                x=[start, end, end, start],
                y=[m - 0.4, m - 0.4, m + 0.4, m + 0.4],
                fill='toself', fillcolor=mode_colors[m - 1],
                opacity=0.35, line=dict(width=0),
                name=mode_labels[m - 1], legendgroup=mode_labels[m - 1],
                showlegend=bool(start == seg_starts[0]) if seg_starts else False,
                hoverinfo='skip'))

    fig.update_layout(
        title='PMS Operating Mode Timeline',
        xaxis_title='Time (days)',
        yaxis=dict(tickvals=list(range(1, 7)), ticktext=mode_labels, range=[0.5, 6.5]),
        height=400, hovermode='closest')
    return fig


def plot_dr_activation(results):
    """DR activation timeline (PeakClip / ValleyFill)."""
    modes = np.array(results.dr_mode)
    t = np.arange(len(modes)) / 24.0
    clip_idx = modes == 'PeakClip'
    fill_idx = modes == 'ValleyFill'
    y = np.zeros(len(modes))
    y[clip_idx] = 1
    y[fill_idx] = -1

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=t, y=y, mode='markers',
        marker=dict(color=np.where(clip_idx, '#59A14F', '#F28E2B'),
                    size=6, symbol=np.where(clip_idx, 'triangle-down', 'triangle-up')),
        name='DR Events'))

    fig.update_layout(title='Demand Response Activation',
                      xaxis_title='Time (days)',
                      yaxis=dict(tickvals=[-1, 0, 1],
                                 ticktext=['ValleyFill', 'Off', 'PeakClip']),
                      height=300)
    return fig
