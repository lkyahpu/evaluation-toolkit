# -*- coding: utf-8 -*-

############################################################################
#  This file is part of the 4D Light Field Benchmark.                      #
#                                                                          #
#  This work is licensed under the Creative Commons                        #
#  Attribution-NonCommercial-ShareAlike 4.0 International License.         #
#  To view a copy of this license,                                         #
#  visit http://creativecommons.org/licenses/by-nc-sa/4.0/.                #
#                                                                          #
#  Authors: Katrin Honauer & Ole Johannsen                                 #
#  Contact: contact@lightfield-analysis.net                                #
#  Website: www.lightfield-analysis.net                                    #
#                                                                          #
#  The 4D Light Field Benchmark was jointly created by the University of   #
#  Konstanz and the HCI at Heidelberg University. If you use any part of   #
#  the benchmark, please cite our paper "A dataset and evaluation          #
#  methodology for depth estimation on 4D light fields". Thanks!           #
#                                                                          #
#  @inproceedings{honauer2016benchmark,                                    #
#    title={A dataset and evaluation methodology for depth estimation on   #
#           4D light fields},                                              #
#    author={Honauer, Katrin and Johannsen, Ole and Kondermann, Daniel     #
#            and Goldluecke, Bastian},                                     #
#    booktitle={Asian Conference on Computer Vision},                      #
#    year={2016},                                                          #
#    organization={Springer}                                               #
#    }                                                                     #
#                                                                          #
############################################################################

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np

from utils import misc, plotting
from utils.logger import log
import settings
from metrics import MAEContinSurf, MAEPlanes, Quantile, BadPix


SUBDIR = "metric_overviews"


def plot_normals(algorithms, scenes, n_rows=2, subdir=SUBDIR, fs=15):

    # prepare figure grid
    n_entries_per_row = int(np.ceil((len(algorithms) + 1) / float(n_rows)))
    n_vis_types = 3

    rows, cols = (n_vis_types * n_rows), n_entries_per_row + 1
    hscale, wscale = 5, 7

    # initialize metrics
    metric_mae_contin = MAEContinSurf()
    metric_mae_planes = MAEPlanes()

    for scene in scenes:
        h, w = scene.get_height(), scene.get_width()

        # prepare figure and colorbar size
        fig = plt.figure(figsize=(cols * 1.7, 1.45 * rows * 1.5))
        grids = gridspec.GridSpec(rows, cols, height_ratios=[hscale] * rows, width_ratios=[wscale] * (cols - 1) + [1])
        cb_height = h
        cb_width = w / float(wscale)

        # some scenes have no evaluation mask for planar, non-planar or both surfaces
        try:
            mask_contin = metric_mae_contin.get_evaluation_mask(scene)
        except IOError:
            log.info("No evaluation mask found for non-planar continuous surfaces on: %s" % scene.get_display_name())
            mask_contin = np.zeros((h, w), dtype=np.bool)
        try:
            mask_planes = metric_mae_planes.get_evaluation_mask(scene)
        except IOError:
            log.info("No evaluation mask found for planar continuous surfaces on: %s" % scene.get_display_name())
            mask_planes = np.zeros((h, w), dtype=np.bool)

        # plot ground truth column
        gt = scene.get_gt()
        _plot_normals_entry(scene,  gt, gt, mask_planes, mask_contin, "GT",
                            metric_mae_contin, metric_mae_planes,
                            0, grids, n_entries_per_row, n_vis_types, cols, cb_height, cb_width, fs=fs)

        # plot algorithm columns
        for idx_a, algorithm in enumerate(algorithms):
            algo_result = misc.get_algo_result(scene, algorithm)

            _plot_normals_entry(scene, algo_result, gt, mask_planes, mask_contin, algorithm.get_display_name(),
                                metric_mae_contin, metric_mae_planes,
                                idx_a + 1, grids, n_entries_per_row, n_vis_types, cols, cb_height, cb_width, fs=fs)

        plt.suptitle("Angular Error: non-planar / planar surfaces", fontsize=fs)

        # save figure
        fig_path = plotting.get_path_to_figure("normals_%s" % scene.get_name(), subdir=subdir)
        plotting.save_tight_figure(fig, fig_path, hide_frames=True, remove_ticks=True, hspace=0.03, wspace=0.03)


def _plot_normals_entry(scene, disp_map, gt, mask_planes, mask_contin, algo_name,
                        metric_mae_contin, metric_mae_planes,
                        idx, grids, entries_per_row, nn, cols, cb_height, cb_widthg, fs):

    add_ylabel = not idx % entries_per_row  # is first column
    add_colorbar = not ((idx + 1) % entries_per_row)  # is last column
    idx_row = (idx / entries_per_row) * nn
    idx_col = idx % entries_per_row

    # plot disparity map
    plt.subplot(grids[idx_row * cols + idx_col])
    cb = plt.imshow(disp_map, **settings.disp_map_args(scene))
    plt.title(algo_name, fontsize=fs)

    if add_ylabel:
        plt.ylabel("DispMap", fontsize=fs)
    if add_colorbar:
        plotting.add_colorbar(grids[idx_row * cols + idx_col + 1], cb, cb_height, cb_widthg,
                              colorbar_bins=7, fontsize=fs)

    # plot normal map
    plt.subplot(grids[(idx_row + 1) * cols + idx_col])
    plt.imshow(scene.get_normal_vis_from_disp_map(disp_map))

    if add_ylabel:
        plt.ylabel("Normals", fontsize=fs)

    # plot angular errors
    plt.subplot(grids[(idx_row + 2) * cols + idx_col])

    # compute angular errors
    try:
        score_contin = "%0.2f" % metric_mae_contin.get_score(disp_map, gt, scene)
    except IOError:
        score_contin = "-"

    try:
        score_planes = "%0.2f" % metric_mae_planes.get_score(disp_map, gt, scene)
    except IOError:
        score_planes = "-"

    plt.title("%s / %s" % (score_contin, score_planes), fontsize=fs)

    if add_ylabel:
        plt.ylabel("Angular Error", fontsize=fs)

    # get combined error visualization (if applicable)
    mask = mask_contin + mask_planes
    if np.sum(mask) > 0:
        _, vis_normals = metric_mae_contin.get_score_from_mask(disp_map, gt, scene, mask, with_visualization=True)
        cb = plt.imshow(vis_normals, **settings.metric_args(metric_mae_contin))

        if add_colorbar:
            plotting.add_colorbar(grids[(idx_row + 2) * cols + idx_col + 1], cb, cb_height, cb_widthg,
                                  colorbar_bins=7, fontsize=fs)


def plot_general_overview(algorithms, scenes, metrics, fig_name=None, subdir=SUBDIR, fs=11):
    n_vis_types = len(metrics)

    # prepare figure grid
    rows, cols = len(scenes)*n_vis_types, len(algorithms)+1
    hscale, wscale = 5, 7
    grids = gridspec.GridSpec(rows, cols, height_ratios=[hscale] * rows, width_ratios=[wscale] * (cols-1) + [1])
    fig = plt.figure(figsize=(cols * 1.4, 1.15 * rows * 1.6))

    cb_height, w = scenes[0].get_height(), scenes[0].get_width()
    cb_width = w / float(wscale)

    for idx_s, scene in enumerate(scenes):
        gt = scene.get_gt()

        for idx_a, algorithm in enumerate(algorithms):
            algo_result = misc.get_algo_result(scene, algorithm)

            for idx_m, metric in enumerate(metrics):
                score, vis = metric.get_score(algo_result, gt, scene, with_visualization=True)

                plt.subplot(grids[(n_vis_types*idx_s+idx_m)*cols + idx_a])
                cb = plt.imshow(vis, **settings.metric_args(metric))

                # add algorithm name and metric score on top row
                if idx_s == 0 and idx_m == 0:
                    plt.title("%s\n%0.2f" % (algorithm.get_display_name(), score), fontsize=fs)
                else:
                    plt.title("%0.2f" % score, fontsize=fs)

                # add metric name to first column
                if idx_a == 0:
                    plt.ylabel(metric.get_display_name())

                # add colorbar to last column
                if idx_a == len(algorithms) - 1:
                    plotting.add_colorbar(grids[(n_vis_types*idx_s+idx_m)*cols + idx_a + 1], cb, cb_height, cb_width,
                                          colorbar_bins=metric.colorbar_bins, fontsize=fs)

    # save figure
    if fig_name is None:
        fig_name = "metric_overview_" + "_".join(metric.get_identifier() for metric in metrics)
    fig_path = plotting.get_path_to_figure(fig_name, subdir=subdir)
    plotting.save_tight_figure(fig, fig_path, hide_frames=True, remove_ticks=True, hspace=0.01, wspace=0.01)