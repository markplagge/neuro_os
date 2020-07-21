import nengo
import numpy as np
import math

def a_gt_b():
    a_gt = nengo.Network()
    with a_gt:
        if_gt_than = nengo.Ensemble(50, dimensions=2, intercepts=nengo.dists.Uniform(0.9, 1.0))

        bg_re_enc = nengo.Ensemble(256, dimensions=2)
        bg = nengo.networks.BasalGanglia(dimensions=2)
        in_a = nengo.Node(size_in=1, size_out=1)
        in_b = nengo.Node(size_in=1, size_out=1)

        out_ga = nengo.Node(size_in=1)
        nengo.Connection(in_a, bg.input[0])
        nengo.Connection(in_b, bg.input[1])

        # nengo.Connection(bg.output, out_ga)
        def gt(x):
            out = [0, 0]
            test1 = np.power(x, 2)
            if test1[0] > 1:
                return [1, 1]
            elif test1[0] > test1[1]:
                return [1, 1]
            elif x[0] > x[1]:
                return [1, 1]
            elif x[0] == x[1]:
                return [0, 0]
            return out

        thm = nengo.networks.Thalamus(2, n_neurons_per_ensemble=128)
        nengo.Connection(bg.output, thm.input)
        nengo.Connection(thm.output, bg_re_enc)
        nengo.Connection(bg_re_enc, if_gt_than, function=gt)
        nengo.Connection(if_gt_than[0], out_ga, synapse=0.01)

        a_gt.output = out_ga
        a_gt.a = in_a
        a_gt.b = in_b
        a_gt.if_gt = if_gt_than
        a_gt.bg_re_enc = bg_re_enc
    return a_gt


def a_eq_b(rel_tol=None):
    a_eq = nengo.Network()

    with a_eq:
        in_a = nengo.Node(size_in=1, size_out=1)
        in_b = nengo.Node(size_in=1, size_out=1)
        if rel_tol is None:
            rel_tol = 0.5

        def base_eq(x):
            if (math.isclose(x[0], x[1], rel_tol=rel_tol)):
                return [1, 1]
            return [0, 0]

        comparitor = nengo.Ensemble(10, dimensions=2)
        compare_enc_a = nengo.Ensemble(256, dimensions=1)
        compare_enc_b = nengo.Ensemble(256, dimensions=1)
        blender = nengo.Ensemble(512, dimensions=2)
        pre_blend = nengo.Ensemble(512, dimensions=2)
        post_blend = nengo.Ensemble(256, dimensions=2)

        output = nengo.Node(size_in=2, size_out=2)
        a_eq.a = in_a
        a_eq.b = in_b
        a_eq.output = output
        a_eq.comparitor = comparitor
        a_eq.comp_enc_a = compare_enc_a
        a_eq.comp_enc_b = compare_enc_b
        a_eq.blend = blender
        a_eq.post_b = post_blend

        nengo.Connection(in_a, compare_enc_a)
        nengo.Connection(in_b, compare_enc_b)
        nengo.Connection(compare_enc_a, pre_blend[0])
        nengo.Connection(compare_enc_b, pre_blend[1])

        nengo.Connection(pre_blend, blender)

        nengo.Connection(blender, comparitor)

        nengo.Connection(comparitor, post_blend, function=base_eq)

        nengo.Connection(post_blend, output, function=base_eq)
    return a_eq

