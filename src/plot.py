# -*- coding: utf-8 -*-
# Credits: Benjamin Dartigues, Emmanuel Bouilhol, Hayssam Soueidan, Macha Nikolski

# These functions are specific for plotting the results produced by the analysis scripts

import matplotlib
from loguru import logger
from scipy.interpolate import interp1d

import constants
from mpi_calculator import DensityStats
from path import global_root_dir

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import interpolate
import scipy.stats as stats
import pandas as pd
import helpers
import pathlib
import numpy as np
from statannot import add_stat_annotation

pd.set_option('display.max_rows', 1000)


def bar_profile_median_timepoints(df: pd.DataFrame, palette, figname, gene, fixed_yscale=0):
    """
    Plots a barplot for 'd_of_c' column for 2 molecules at each timepoint for gene
    Dataframe df contains:
       - 'd_of_c' column to be plotted
       - 'Molecule' column containing either 'mrna' or 'protein'
       - 'Timepoint' column providing the timepoints where they are measured
       - 'error' column for sem error from the median
       - 'CI' column for the confidence interval
    palette is a dict with keys 'mrna' and 'protein'
    fixed_yscale are for setting the y_scale upper limit
    """
    bar_width = 0.35
    fig, ax = plt.subplots()
    labels = np.sort(df["Timepoint"].unique())
    index = np.arange(len(labels))
    df[['lower', 'higher']] = pd.DataFrame(df['CI'].to_list(), columns=['lower', 'higher'], index=df.index)
    dfs = df.sort_values('Timepoint')
    # Fixing readability - scaling up for errors and low values (due to shift)
    dfs.loc[(dfs.error < 0.2), "error"] = dfs['error'] * 2
    dfs = dfs.round({'lower': 1, 'higher': 1})

    mrna = dfs[dfs["Molecule"] == "mrna"]
    protein = dfs[dfs["Molecule"] == "protein"]
    mask = mrna['d_of_c'] != 0
    x_new = np.linspace(index[mask].min(), index[mask].max(), 20)
    f_cubic = interp1d(index[mask], mrna['d_of_c'][mask], kind='cubic')
    ax.plot(x_new, f_cubic(x_new), zorder=5, color=helpers.colorscale("A5073E", 0.9))
    mask = protein['d_of_c'] != 0
    x_new = np.linspace(np.min([index[mask] + bar_width]), np.max([index[mask] + bar_width]), 20)
    f_cubic = interp1d(index[mask] + bar_width, protein['d_of_c'][mask], kind='cubic')
    ax.plot(x_new, f_cubic(x_new), zorder=5, color=helpers.colorscale("A5073E", 1.2))

    ax.bar(index, mrna["d_of_c"], bar_width, yerr=mrna["error"], color=palette["mrna"], error_kw=dict(elinewidth=6, ecolor='black'))
    ax.bar(index + bar_width, protein["d_of_c"], bar_width, yerr=protein["error"], color=palette["protein"], error_kw=dict(elinewidth=6, ecolor='black'))

    plt.ylim([0, fixed_yscale])
    ax.set_xlabel("", fontsize=15)
    ax.set_ylabel("", fontsize=15)
    ax.yaxis.grid(which="major", color='black', linestyle='-', linewidth=0.25)
    plt.yticks(fontsize=20)
    plt.xticks(fontsize=20)
    all_timepoints = np.sort(list(set(mrna['Timepoint']) | set(protein['Timepoint'])))
    plt.xticks(index + bar_width / 2, all_timepoints, fontsize=20)

    # create the table for the CI
    CI = pd.DataFrame({"mRNA": mrna[["lower", "higher"]].values.tolist(),
                       "protein": protein[["lower", "higher"]].values.tolist()}, index=all_timepoints)
    CI = CI.T
    plt.table(cellText=CI.values,
              rowLabels=CI.index.values,
              colLabels=list(str(' ') * len(all_timepoints)),  # empty since we already have the xticks
              loc='bottom',
              bbox=[0.0, -0.3, 1, .28])
    plt.subplots_adjust(bottom=0.28)
    fig.savefig(figname, format='png')
    plt.close()
    logger.info("Generated image at {}", str(figname).split("analysis/")[1])


def bar_profile_median(data_median, err, molecule_type, plot_xlabels, figname,
                       confidence_interval=None, annot=False, test='t-test_ind', data_to_annot={}):
    """
    Plot a barplot for each gene with height given by medians, error bars defined by err
    and confidence intervals by CI; CI is a dictionary with keys = genes
    test: a string (t-test_ind, t-test_welch, t-test_paired, etc)
    """
    # Define plot variables
    all_genes = list(data_median.keys())
    medians = list(data_median.values())
    plot_colors = constants.analysis_config['PLOT_COLORS']
    bar_width = 0.35
    ind = np.arange(len(all_genes))
    fig, ax = plt.subplots()

    # Search for ymin and y max
    y_max = np.max(medians) + np.nanmin(medians) / 10
    y_min = 0 # np.float(np.nanmin(list(medians))) - (np.float(np.nanmin(list(medians))) / 5)
    plt.ylim([y_min, y_max])

    if annot:
        add_annot(data_to_annot, all_genes, ax, test)

    ax.set_xlabel("", fontsize=15)
    ax.set_ylabel("", fontsize=10)
    ax.yaxis.grid(which="major", color='black', linestyle='-', linewidth=0.25)
    plt.yticks(fontsize=20)
    plt.xticks(fontsize=10)
    plt.xticks(ind, all_genes, fontsize=10)
    ax.tick_params(right=False, top=False, bottom=True, direction='out', length=8, width=3, colors='black')
    ax.spines['left'].set_linewidth(3)
    ax.bar(ind, medians, bar_width, color=plot_colors, yerr=err)
    ax.set_xticklabels(plot_xlabels)

    # create the table for the confidence intervals
    if confidence_interval is not None:
        assert all_genes == list(confidence_interval.keys())
        CI_df = pd.DataFrame(confidence_interval.values(), columns=['lower', 'higher'], index=all_genes)
        CI_df = CI_df.round({'lower': 1, 'higher': 1})
        CI_df = pd.DataFrame({molecule_type: CI_df[["lower", "higher"]].values.tolist()}, index=all_genes)
        CI_df = CI_df.T
        CI_table = plt.table(cellText=CI_df.values, rowLabels=CI_df.index.values,
                             colLabels=[lab for lab in plot_xlabels],  # empty since we already have the xticks
                             loc='bottom', cellLoc='center', bbox=[0.0, -0.3, 1, .28])
        plt.subplots_adjust(bottom=0.28, left=0.15)
        CI_table.auto_set_font_size(False)
        CI_table.set_fontsize(12)
        ax.set_xticks([])

    ax.set_xlim(-0.5, len(ind) - 0.5)
    fig.savefig(figname)
    plt.close()


def bar_profile(data, figname, plot_colors):
    fig, ax = plt.subplots()
    ax.tick_params(right=False, top=False, bottom=False, direction='inout', length=8, width=3, colors='black')
    for axis in ['left']:
        ax.spines[axis].set_linewidth(3)
    plt.yticks(fontsize=20)
    ax.yaxis.grid(True, linestyle='-', which='major', color='lightgrey', alpha=0.5)
    bar_width = 0.35
    x_component = np.arange(len(data))
    ax.bar(x_component, data, bar_width, color=plot_colors)

    # Search for ymin and y max
    y_max = np.float(np.max(data)) + (np.float(np.nanmin(data)) / 10)
    y_min = np.float(np.nanmin(data)) - (np.float(np.nanmin(data)) / 5)
    plt.ylim([y_min, y_max])

    ax.set_xticks(x_component)
    ax.set_xlim(-0.5, len(data) - 0.5)
    ax.set_xticklabels(["" for i in range(0, len(data))])
    plt.savefig(figname, format='png')
    plt.close()
    logger.info("Generated image at {}", str(figname).split("analysis/")[1])


def violin_profile(dictionary, tgt_fp, xlabels, rotation=0, annot=False):
    genes = constants.analysis_config['MRNA_GENES']
    dd = pd.DataFrame({k: pd.Series(v).astype(float)
                       for k, v in dictionary.items()}).melt().dropna().rename(columns={"variable": "gene"})
    my_pal = {}
    for i, color in enumerate(constants.analysis_config['PLOT_COLORS'][0:len(genes)]):
        my_pal[genes[i]] = color

    sns_violinplot(dd, my_pal, tgt_fp, xlabels, x='gene', no_legend=False, rotation=rotation, annot=annot)


def sns_barplot(dd, my_pal, figname, x="Timepoint", y="MPI", hue="Molecule_type", err="err"):
    fig, ax = plt.subplots()
    ax.yaxis.grid(True, linestyle='-', which='major', color='lightgrey', alpha=0.5)
    ax.tick_params(right=False, top=False, bottom=False, direction='inout', length=8, width=3, colors='black')
    ax.spines['left'].set_linewidth(3)
    plt.yticks(fontsize=20)
    idx1 = np.arange(dd["Timepoint"].nunique())
    width = 0.35
    idx2 = [x + width for x in idx1]
    x_labels = sorted(dd["Timepoint"].unique())
    mrna_values = list(dd[dd["Molecule_type"] == "mrna"][y])
    mrna_err = list(dd[dd["Molecule_type"] == "mrna"][err])
    protein_values = list(dd[dd["Molecule_type"] == "protein"][y])
    protein_err = list(dd[dd["Molecule_type"] == "protein"][err])
    protein_err = [x if (float(x) < 0.0000000000001) else 0.05 for x in protein_err]
    mrna_err = [x if (float(x) < 0.0000000000001) else 0.05 for x in mrna_err]
    assert (len(mrna_values) == len(protein_values))
    assert (len(mrna_values) == len(mrna_err))

    mrna = dd[dd["Molecule_type"] == "mrna"]
    labels = np.sort(dd["Timepoint"].unique())
    index = np.arange(len(labels))

    mask = mrna['MPI'] != 0
    x_new = np.linspace(index[mask].min(), index[mask].max(), 20)
    f_cubic = interp1d(index[mask], mrna['MPI'][mask], kind='cubic')
    ax.plot(x_new, f_cubic(x_new), zorder=5, color=helpers.colorscale("A5073E", 0.9))
    protein = dd[dd["Molecule_type"] == "protein"]
    mask = protein['MPI'] != 0
    x_new = np.linspace(np.min([index[mask] + width]), np.max([index[mask] + width]), 20)
    f_cubic = interp1d(index[mask] + width, protein['MPI'][mask], kind='cubic')
    ax.plot(x_new, f_cubic(x_new), zorder=5, color=helpers.colorscale("A5073E", 1.2))

    ax.bar(idx1, mrna_values, width, color=my_pal["mrna"],
           yerr=mrna_err, error_kw=dict(elinewidth=1, ecolor='black'))
    ax.bar(idx2, protein_values, width, color=my_pal["protein"],
           yerr=protein_err, error_kw=dict(elinewidth=1, ecolor='black'))
    ax.set_xlim(-width, len(idx1) + width)
    #    ax.set_ylim(-1, 1)
    ax.set_xticks(idx1 + width / 2)
    plt.yticks(fontsize=20)
    plt.xticks(fontsize=20)
    ax.set_xticklabels(x_labels)
    fig.savefig(figname)
    plt.close()


def sns_linear_regression(data_1, data_2, color, graph_file_path_name, order=1):
    sns.set(style="white", color_codes=True)
    annot_kws = {'prop': {'family': 'monospace', 'weight': 'bold', 'size': 8}}
    res1 = stats.pearsonr(data_1, data_2)
    sns.set(font_scale=1)
    sns_plot_regression = sns.jointplot(x=np.log(data_1), y=np.log(data_2), order=order, kind='reg',
                                        x_estimator=np.mean, color=color)
    sns_plot_regression.ax_marg_x.set_xlim(6, 8)
    phantom, = sns_plot_regression.ax_joint.plot([], [], linestyle="", alpha=0)
    sns_plot_regression.ax_joint.legend([phantom], [
        'pearsonr={:f}, R' + chr(0x00B2) + '={:f}, p={:.2E}'.format(res1[0], res1[0] ** 2, res1[1])], **annot_kws)
    sns_plot_regression.savefig(graph_file_path_name, format="png")


def sns_violinplot(dd, my_pal, figname, plot_xlabels, x="Gene", y='value',
                   hue=None, no_legend=True, rotation=0, annot=False):
    fig = plt.figure(figsize=(10, 10))
    ax = sns.violinplot(x=x, y=y, data=dd, hue=hue, palette=my_pal, cut=0)
    gene_list = constants.analysis_config['MRNA_GENES']
    if annot:
        box_pairs = []
        for i in range(1, len(gene_list) + 1):
            if i % 2 == 0:
                box_pairs.append(((gene_list[i - 2], gene_list[i - 1])))
        add_stat_annotation(ax, data=dd, x=x, y=y, hue=hue,
                            box_pairs=box_pairs,
                            test='t-test_ind', text_format='star', loc='inside', verbose=2)

    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.yaxis.grid(which="major", color='black', linestyle='-', linewidth=0.25)
    ax.tick_params(right=False, top=False, direction='out', length=8, width=3, colors='black')
    ax.spines['left'].set_linewidth(3)
    ax.set_xticklabels(plot_xlabels, rotation=rotation)
    plt.yticks(fontsize=30)
    plt.xticks(fontsize=20)
    plt.gcf().subplots_adjust(bottom=0.2, left=0.2)
    if no_legend:
        ax.legend_.remove()
    fig.savefig(figname, format='png')
    plt.close()


def sns_boxplot(dd, my_pal, figname, x="Gene", y="value", hue='Quadrants'):
    fig, ax = plt.subplots()
    box = sns.boxplot(x=x, y=y, data=dd, palette=my_pal)
    box.set_xlabel("", fontsize=15)
    box.set_ylabel("", fontsize=15)
    box.yaxis.grid(which="major", color='black', linestyle='-', linewidth=0.25)
    box.tick_params(right=False, top=False, direction='inout', length=8, width=3, colors='black')
    plt.yticks(fontsize=15)
    fig.savefig(figname, format='png')
    plt.close()


def plot_boxplot_MPI(mrna_density_stats: DensityStats, protein_density_stats: DensityStats,
                     molecule_list, mrna_timepoint_list, protein_timepoint_list):
    """
    The timepoint_list has to have the same order as in the mpi() function
    """
    plot_colors = constants.analysis_config['PLOT_COLORS']
    mrna_density_stats.update_group_key(['Timepoint'])
    protein_density_stats.update_group_key(['Timepoint'])

    for color_num, gene in enumerate(molecule_list):
        # Collect mrna and protein density statistics for this gene only
        dd = {'Molecule_type': [], 'Timepoint': [], 'MPI': [], 'err': []}
        gene_stats = mrna_density_stats.subset_stats("Gene", gene)
        prot_stats = protein_density_stats.subset_stats("Gene", gene)
        mrna_mpis, mrna_errs = gene_stats.mpi()
        prot_mpis, prot_errs = prot_stats.mpi()
        dd["MPI"] = mrna_mpis + prot_mpis
        dd["err"] = mrna_errs + prot_errs
        dd["Molecule_type"] = ["mrna"] * len(mrna_timepoint_list) + ["protein"] * len(protein_timepoint_list)
        dd["Timepoint"] = sorted(mrna_timepoint_list) + sorted(protein_timepoint_list)
        for tp in np.setdiff1d(mrna_timepoint_list, protein_timepoint_list):
            dd["Timepoint"].append(tp);
            dd["Molecule_type"].append("protein")
            dd["MPI"].append(0);
            dd["err"].append(0)
        for tp in np.setdiff1d(protein_timepoint_list, mrna_timepoint_list):
            dd["Timepoint"].append(tp);
            dd["Molecule_type"].append("mrna")
            dd["MPI"].append(0);
            dd["err"].append(0)

        df = pd.DataFrame(dd)
        df.sort_values("Timepoint", axis=0, ascending=True, inplace=True)

        tgt_image_name = constants.analysis_config['FIGURE_NAME_FORMAT_DYNAMIC_MPI'].format(gene=gene)
        tgt_fp = pathlib.Path(constants.analysis_config['FIGURE_OUTPUT_PATH'].format(root_dir=global_root_dir),
                              tgt_image_name)

        my_pal = {"mrna": str(plot_colors[color_num]),
                  "protein": str(helpers.color_variant(plot_colors[color_num], +80))}
        helpers.create_dir_if_needed_for_filepath(tgt_fp)
        sns_barplot(df, my_pal, tgt_fp, y="MPI", err="err")
        logger.info("Generated image at {}", str(tgt_fp).split("analysis/")[1])


def sns_barplot(dd, my_pal, figname, y="MPI", err="err"):
    fig, ax = plt.subplots()
    ax.yaxis.grid(True, linestyle='-', which='major', color='lightgrey', alpha=0.5)
    ax.tick_params(right=False, top=False, bottom=False, direction='inout', length=8, width=3, colors='black')
    ax.spines['left'].set_linewidth(3)
    plt.yticks(fontsize=20)
    idx1 = np.arange(dd["Timepoint"].nunique())
    width = 0.35
    idx2 = [x + width for x in idx1]
    x_labels = sorted(dd["Timepoint"].unique())
    mrna_values = list(dd[dd["Molecule_type"] == "mrna"][y])
    mrna_err = list(dd[dd["Molecule_type"] == "mrna"][err])
    protein_values = list(dd[dd["Molecule_type"] == "protein"][y])
    protein_err = list(dd[dd["Molecule_type"] == "protein"][err])
    assert (len(mrna_values) == len(protein_values))
    assert (len(mrna_values) == len(mrna_err))

    mrna = dd[dd["Molecule_type"] == "mrna"]
    labels = np.sort(dd["Timepoint"].unique())
    index = np.arange(len(labels))

    mask = mrna['MPI'] != 0
    x_new = np.linspace(index[mask].min(), index[mask].max(), 20)
    f_cubic = interp1d(index[mask], mrna['MPI'][mask], kind='cubic')
    ax.plot(x_new, f_cubic(x_new), zorder=5, color=helpers.colorscale("A5073E", 0.9))
    protein = dd[dd["Molecule_type"] == "protein"]
    mask = protein['MPI'] != 0
    x_new = np.linspace(np.min([index[mask] + width]), np.max([index[mask] + width]), 20)
    f_cubic = interp1d(index[mask] + width, protein['MPI'][mask], kind='cubic')
    ax.plot(x_new, f_cubic(x_new), zorder=5, color=helpers.colorscale("A5073E", 1.2))

    ax.bar(idx1, mrna_values, width, color=my_pal["mrna"],
           yerr=mrna_err, error_kw=dict(elinewidth=1, ecolor='black'))
    ax.bar(idx2, protein_values, width, color=my_pal["protein"],
           yerr=protein_err, error_kw=dict(elinewidth=1, ecolor='black'))
    ax.set_xlim(-width, len(idx1) + width)
    #    ax.set_ylim(-1, 1)
    ax.set_xticks(idx1 + width / 2)
    plt.yticks(fontsize=20)
    plt.xticks(fontsize=20)
    ax.set_xticklabels(x_labels)
    fig.savefig(figname)
    plt.close()


def plot_MPI(density_stats: DensityStats, molecule_type, figname):
    labels = density_stats.make_labels()
    mpis, errs = density_stats.mpi()
    gene_2_mpis = {}
    for i in range(len(labels)):
        gene_2_mpis[labels[i]] = np.float(mpis[i])

    bar_profile_median(gene_2_mpis, errs, molecule_type, labels, figname)


def compute_violin_plot_ratio(density_stats: DensityStats, molecule_type, figname,
                              limit_threshold=6, groupby_key=['Gene'], term=""):
    df = density_stats.df
    if term != "":
        df[groupby_key[0]] = df.apply(lambda row: term if term[2:len(term)] in row[groupby_key[0]] else row[groupby_key[0]], axis=1)
    groups = [tp for tp, line in df.groupby(groupby_key, sort=False)]
    df["MTOC_ratio"] = df.apply(lambda row: row['MTOC'] / row.filter(regex=("Non MTOC.*")).mean() if row.filter(
        regex=("Non MTOC.*")).mean() != 0 else 0.0, axis=1)
    dd = pd.melt(df, id_vars=groupby_key[0], value_vars=["MTOC_ratio"], var_name='Quadrants')
    dd = dd.replace(0.000000, np.nan)
    dd.dropna(inplace=True)

    my_pal = {}
    for i, color in enumerate(constants.analysis_config['PLOT_COLORS'][0:len(groups)]):
        my_pal[groups[i]] = color
    outliers = helpers.detect_outliers(np.array(dd["value"]), limit_threshold)
    dd = dd[~np.isin(dd["value"], outliers)]  # dd[dd["value"] < limit_threshold]
    if molecule_type == 'mrna':
        xlabels = constants.analysis_config['MRNA_GENES_LABEL']
    else:
        xlabels = constants.analysis_config['PROTEINS_LABEL']
    sns_violinplot(dd, my_pal, figname, xlabels, x=groupby_key[0], no_legend=False, rotation=45)


def compute_categorical_violin_plot_ratio(density_stats: DensityStats, molecule_type, figname,
                                          limit_threshold=6, groupby_key=['Gene'], term="", gene=""):
    df = density_stats.df
    if term != "":
        df["Label"] = df.apply(
            lambda row: term if term[2:len(term) - 1] in row[groupby_key[len(groupby_key) - 1]] else 'Control',
            axis=1)

    groups = [tp for tp, line in df.groupby(["Label"], sort=False)]
    df["MTOC_ratio"] = df.apply(lambda row: row['MTOC'] / row.filter(regex=("Non MTOC.*")).mean() if row.filter(
        regex=("Non MTOC.*")).mean() != 0 else 0.0, axis=1)
    dd = pd.melt(df, id_vars=groupby_key[len(groupby_key) - 1], value_vars=["MTOC_ratio"], var_name='Quadrants')
    if term != "":
        dd["Quadrants"] = df["Label"].values
    if gene != "":
        dd["Gene"] = [gene for i in range(len(df["Label"].values))]
    dd = dd.replace(0.000000, np.nan)
    dd.dropna(inplace=True)

    my_pal = {}
    for i, color in enumerate(constants.analysis_config['PLOT_COLORS'][0:len(groups)]):
        my_pal[groups[i]] = color
    outliers = helpers.detect_outliers(np.array(dd["value"]), limit_threshold)
    dd = dd[~np.isin(dd["value"], outliers)]  # dd[dd["value"] < limit_threshold]
    if molecule_type == 'mrna':
        xlabels = constants.analysis_config['MRNA_GENES_LABEL']
    else:
        xlabels = constants.analysis_config['MRNA_GENES_LABEL'][:4]
    sns_violinplot(dd, my_pal, figname, xlabels, x="Gene", hue="Quadrants")


def compute_violin_plot_enrichment(density_stats: DensityStats, molecule_type, figname,
                                   limit_threshold=6, log=False, groupby_key="Gene"):
    df = density_stats.df
    # melt dataframe and group together all non MTOC quadrant

    value_vars = [density_stats.mtoc_quadrant_label] + density_stats.quadrant_labels
    dd = pd.melt(df, id_vars=[groupby_key], value_vars=value_vars, var_name='Quadrants')
    for label in density_stats.quadrant_labels:
        dd = dd.replace(label, 'Non MTOC')
    dd = dd.replace(0.000000, np.nan)
    outliers = helpers.detect_outliers(np.array(dd["value"]), limit_threshold)
    dd = dd[~np.isin(dd["value"], outliers)]
    dd.dropna(inplace=True)
    # apply log scale
    if (log):
        dd['value'] = dd['value'].apply(np.log2)
    # Choose color palette
    my_pal = {"MTOC": "#66b2ff", "Non MTOC": "#1a8cff"}

    # remove outliers
    if molecule_type == 'mrna':
        xlabels = constants.analysis_config['MRNA_GENES_LABEL']
    else:
        xlabels = constants.analysis_config['MRNA_GENES_LABEL'][:4]
    sns_violinplot(dd, my_pal, figname, xlabels, x=groupby_key, hue=dd['Quadrants'], rotation=45)


def compute_categorical_violin_plot_enrichment(density_stats: DensityStats, molecule_type, figname, limit_threshold=8, log=False,
                                               groupby_key="Gene", term="", gene=""):
    df = density_stats.df
    value_vars = [density_stats.mtoc_quadrant_label] + density_stats.quadrant_labels

    # melt dataframe and group together all non MTOC quadrant
    groups = [tp for tp, line in df.groupby(groupby_key, sort=False)]
    if term != "":
        df[groupby_key] = df.apply(lambda row: term if term[2:len(term)] in row[groupby_key] else row["Gene"], axis=1)

    dd = pd.melt(df, id_vars=[groupby_key], value_vars=value_vars,
                 var_name='Quadrants')
    for label in density_stats.quadrant_labels:
        dd = dd.replace(label, 'Non MTOC')
    if gene != "":
        dd["Gene"] = [gene for i in range(len(df["Label"].values))]
    dd = dd.replace(0.000000, np.nan)
    outliers = helpers.detect_outliers(np.array(dd["value"]), limit_threshold)
    dd = dd[~np.isin(dd["value"], outliers)]  # dd[dd["value"] < limit_threshold]
    dd.dropna(inplace=True)
    # apply log scale
    if (log):
        dd['value'] = dd['value'].apply(np.log2)
    # Choose color palette
    my_pal = {"MTOC": "#66b2ff", "Non MTOC": "#1a8cff"}

    # remove outliers
    if molecule_type == 'mrna':
        xlabels = constants.analysis_config['MRNA_GENES_LABEL']
    else:
        xlabels = constants.analysis_config['MRNA_GENES_LABEL'][:4]
    sns_violinplot(dd, my_pal, figname, xlabels, x=groupby_key, hue=dd['Quadrants'])


def profile(profiles, genes, num_contours, figname):
    plot_colors = constants.analysis_config['PLOT_COLORS']
    fig = plt.figure(figsize=(15, 10))
    ax = fig.add_subplot(111)
    ax.yaxis.grid(which="major", color='black', linestyle='-', linewidth=0.25)
    ax.tick_params(right=False, top=False, direction='inout', length=8, width=3, colors='black')
    for axis in ['bottom', 'left']:
        ax.spines[axis].set_linewidth(3)
    plt.yticks(fontsize=30)
    plt.xticks(fontsize=30)
    plt.xticks([w for w in range(0, num_contours + 2, 10)])
    for i, gene in enumerate(genes):
        plt.plot(np.arange(num_contours), profiles[gene], color=plot_colors[i], linewidth=3, label=genes)
    plt.savefig(figname)
    plt.close()


def plot_figure(total_mads_arhgdia, total_mads_arhgdia_cultured, figname):
    fig, ax = plt.subplots()
    ax.tick_params(right=False, top=False, bottom=False, direction='inout', length=8, width=3, colors='black')
    for axis in ['left']:
        ax.spines[axis].set_linewidth(3)
    plt.yticks(fontsize=20)
    plt.xticks(fontsize=20)
    ax.yaxis.grid(True, linestyle='-', which='major', color='lightgrey', alpha=0.5)
    plt.plot(np.mean(total_mads_arhgdia, axis=0), color='blue')
    plt.plot(np.mean(total_mads_arhgdia_cultured, axis=0), color='black')
    ax.set_xlim(0, len(total_mads_arhgdia[0]))
    plt.savefig(figname)
    plt.close()


def spline_graph(grid_mat, figname, band_n=100):
    fig, ax = plt.subplots()
    x_mrna = np.arange(0, band_n, 0.5)
    fact = np.max(np.array(grid_mat)) / 10
    data = (np.array(grid_mat).flatten() / fact).astype(int) + 1
    spl = interpolate.UnivariateSpline(np.arange(0, band_n, 1), data)
    m_y_new = spl(x_mrna)
    plt.plot(x_mrna, m_y_new)
    ax.set_ylim((0, 12))
    ax.set_xlim((0, band_n - 1))
    plt.savefig(figname)
    plt.close()


def heatmap(grid_mat, figname, band_n=100):
    fig, ax = plt.subplots()
    ax.set_yticks([])
    major_ticks = np.arange(0, int(band_n) + 1, 1)
    ax.tick_params(axis='both', which='major', labelsize=5)
    ax.set_xticks(major_ticks)
    plt.imshow(grid_mat, cmap='coolwarm', aspect=band_n / 3)
    plt.ylim((0, 0.4))
    plt.savefig(figname)
    plt.close()


def compute_heatmap(ranking, gene, figname, size=4, xtickslabel=['2h', '3h', '5h', '7h'], ytickslabel=['2h', '3h', '4h', '5h']):
    fig, ax = plt.subplots()
    im = np.flipud(np.kron(ranking, np.ones((10, 10))))
    plt.imshow(im, extent=[0, size, 0, size], cmap='GnBu', interpolation='nearest')
    ax.set_ylabel("mRNA  - Time (hrs)")
    ax.set_xlabel("Protein  - Time (hrs)")
    myxticklabels = xtickslabel
    ax.xaxis.set(ticks=np.arange(0.5, size + 0.5, 1), ticklabels=myxticklabels)
    myyticklabels = ytickslabel
    ax.yaxis.set(ticks=np.arange(0.5, size + 0.5, 1), ticklabels=myyticklabels)
    ax.set_title(gene)
    plt.savefig(figname)
    plt.close()


def add_annot(data, gene_list, ax, test):
    dd = pd.DataFrame(
        dict([(k, pd.Series(v)) for k, v in data.items()])).melt().dropna().rename(
        columns={"variable": "gene"})
    box_pairs = []
    for i in range(1, len(gene_list) + 1):
        if i % 2 == 0:
            box_pairs.append(tuple((gene_list[i - 2], gene_list[i - 1])))
    # test value should be one of the following:
    add_stat_annotation(ax, data=dd, x='gene', y='value', hue=None,
                        box_pairs=box_pairs,
                        test=test, text_format='star', loc='inside', verbose=2)
