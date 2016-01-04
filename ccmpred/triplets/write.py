import operator
import collections

from ccmpred.raw.ccmraw import stream_or_file


@stream_or_file("w")
def write_triplets(f, raw):
    if 'triplets' not in raw.extra_results:
        raise Exception("Raw data does not have triplets information!")

    if 'x_triplet' not in raw.extra_results:
        raise Exception("Raw data does not have triplet potentials!")

    triplets = raw.extra_results['triplets']
    x_triplet = raw.extra_results['x_triplet']

    triplets = list(zip(triplets, x_triplet))

    triplets.sort(key=operator.itemgetter(1), reverse=True)

    f.write("# {0}\n".format(len(triplets)))
    for coords, score in triplets:
        f.write("{0}\t{1:.8e}\n".format("\t".join("{0}".format(te) for te in coords), score))


@stream_or_file("w")
def write_sum_triplets(f, raw, squared=True):
    if 'triplets' not in raw.extra_results:
        raise Exception("Raw data does not have triplets information!")

    if 'x_triplet' not in raw.extra_results:
        raise Exception("Raw data does not have triplet potentials!")

    triplets = raw.extra_results['triplets']
    x_triplet = raw.extra_results['x_triplet']

    sum_scores = collections.defaultdict(float)

    for (i, j, k, a, b, c), score in zip(triplets, x_triplet):
        if squared:
            score *= score
        sum_scores[(i, j, k)] += score

    sum_scores = list(sum_scores.items())

    sum_scores.sort(key=operator.itemgetter(1), reverse=True)

    f.write("# {0}\n".format(len(sum_scores)))
    for coords, score in sum_scores:
        f.write("{0}\t{1:.8e}\n".format("\t".join("{0}".format(te) for te in coords), score))