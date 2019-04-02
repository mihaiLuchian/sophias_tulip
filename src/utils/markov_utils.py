import numpy as np
import constants as c


def is_listy(thing):
    return hasattr(thing, "__len__")

def listify(thing):
    return thing if is_listy(thing) else [thing]

def simulate_markov_chain(transition_matrix, start_probs, length):

    num_elems = len(transition_matrix)
    r = np.arange(num_elems)
    pseudo_simulations = np.zeros((num_elems,length)).astype('int32')

    for i in range(num_elems):
        s = np.random.choice(r,size=length,p=transition_matrix[i])
        pseudo_simulations[i] = s

    start_elem = np.random.choice(r,p=start_probs)

    simulation = np.zeros(length)
    simulation[0] = start_elem
    current_elem = start_elem

    for i in range(1,length):
        new_elem = pseudo_simulations[current_elem,i]
        simulation[i] = new_elem
        current_elem = new_elem

    return simulation.astype('int32')

def simulate_markov_generator(node, length=None):

    breakout = False
    iteration = 0
    sim_length = 10 if length is None else length
    while breakout == False:
        sim_node = node
        simulation = simulate_markov_chain(
            transition_matrix=sim_node.transition_matrix,
            start_probs=sim_node.start_probs,
            length=sim_length)

        if sim_node.lengths is not None:
            repeats = [ sim_node.lengths[s] for s in simulation  ]
            simulation = np.repeat(simulation,repeats)
        vals = [sim_node.values[i] for i in simulation]


        if sim_node.leaf is False:

            child_lens = np.random.choice(sim_node.child_lengths,sim_length)
            for j,(n,l) in enumerate(zip(vals,child_lens)):
                m = simulate_markov_hierarchy(n,l)
                for i in m:
                    yield i
        else:

            yield np.array(vals)

        iteration += 1
        if length is not None:
            breakout = True


def simulate_markov_processor(node,length):
    m = simulate_markov_hierarchy(node.node,length)
    ms = []
    for i in m:
        ms += [i]

    vals = np.concatenate(ms)
    total_size = vals.size
    # if node.reduce2multiple is not None and total_size >= node.reduce2multiple:
    #     new_len = (total_size//node.reduce2multiple)*node.reduce2multiple
    #     vals = vals[:new_len]

    reps = np.random.choice(node.num_tiles)
    vals = np.tile(vals, reps)

    yield vals


def simulate_markov_hierarchy(node,length=None):
    if node.type == c.TYPE_GEN:
        sim = simulate_markov_generator(node, length)
    elif node.type == c.TYPE_PROC:
        sim = simulate_markov_processor(node,length)
    for i in sim:
        yield i


def paint_linearly_markov_hierarchy(
        markov_tree,
        height, width,
        tile_height = None,
        tile_width = None):
    full_simulation = simulate_markov_hierarchy(markov_tree)

    full_img_len = height * width
    current = 0
    img = np.zeros(height * width)
    for i in full_simulation:
        l = i.size
        img_start = current
        img_end = img_start + l
        gen_end = l
        if img_end >= full_img_len:
            img_end = full_img_len
            gen_end = img_end - img_start

        img[img_start:img_end] = i[:gen_end]
        current = img_end
        if current >= full_img_len - 1:
            break

    if tile_height is not None and tile_width is not None:
        img = img.reshape((-1,tile_width))
        new_img = np.zeros((height,width),dtype=img.dtype)
        num_tiles_h = height//tile_height
        num_tiles_w = width//tile_width
        for i in range(num_tiles_h):
            for j in range(num_tiles_w):
                start_h = i*tile_height
                start_w = j*tile_width
                s = np.s_[start_h:start_h+tile_height,start_w:start_w+tile_width]

                idx = (i*num_tiles_w + j)*tile_height
                new_img[s] = img[idx:idx+tile_height,:]

        return new_img
    else:
        return img.reshape((height,width))


class MarkovModel:

    def __init__(self,
                 preference_matrix=None,
                 start_probs=None,
                 values=None,
                 child_lengths=None,
                 lenghts=None):

        l = len(values)
        self.values = listify(values)

        # child_lengths is one way one can deduce if is leaf node or not
        if child_lengths is None:
            self.child_lengths = None
        else:
            self.child_lengths = listify(child_lengths)
        self.leaf = True if self.child_lengths is None else False
        self.__init_transition_matrix__(preference_matrix)
        self.lengths = lenghts
        self.type = c.TYPE_GEN

        if start_probs is None:
            self.start_probs = np.ones(l)/l
        elif is_listy(start_probs):
            self.start_probs = start_probs
        else:
            self.start_probs = np.zeros(l)
            self.start_probs[start_probs] = 1


    def __init_transition_matrix__(self,preference_matrix):
        self.preference_matrix = preference_matrix
        sums = np.sum(preference_matrix,axis=1)
        self.transition_matrix = self.preference_matrix / sums[:,None]


class SimpleProgression(MarkovModel):

    def __init__(self,
                 values = None,
                 child_lengths = None,
                 lengths=None,
                 start_probs=None):

        values = listify(values)
        l = len(values)
        preference_matrix = np.eye(l)
        preference_matrix = np.roll(preference_matrix,1,axis=1)

        super().__init__(
            preference_matrix=preference_matrix,
            start_probs=start_probs,
            values=values,
            child_lengths=child_lengths,
            lenghts=lengths)


class SimplePattern(SimpleProgression):

    def __init__(self,
                 pattern = None,
                 candidates = None,
                 lengths = None,
                 child_lengths = None,
                 start_probs=None):

        # example of pattern 001100111101234321


        int_pattern = [int(i) for i in pattern]
        values = [ candidates[i] for i in int_pattern ]
        super().__init__(
            values=values,
            child_lengths=child_lengths,
            lengths=lengths,
            start_probs=start_probs)


class FuzzyProgression(MarkovModel):
    def __init__(self,
                 values = None,
                 child_lengths = None,
                 start_probs = None,
                 positive_shifts = 1,
                 negative_shifts = 0,
                 repeat_factor = 1
                 ):

        l = len(values)

        base = np.eye(l)
        preference_matrix = base*repeat_factor
        for i in range(positive_shifts):
            preference_matrix += np.roll(base,i+1,axis=1)
        for i in range(negative_shifts):
            preference_matrix += np.roll(base,-(i+1),axis=1)

        super().__init__(
            preference_matrix=preference_matrix,
            start_probs=start_probs,
            values=values,
            child_lengths=child_lengths)


class RandomMarkovModel(MarkovModel):

    def __init__(self,
                 values=None,
                 child_lengths=None,
                 lengths = None,
                 start_probs=None):


        values = listify(values)
        l = len(values)
        preference_matrix = np.random.choice(
            np.arange(100),size=(l,l))

        super().__init__(
            preference_matrix=preference_matrix,
            start_probs=start_probs,
            values=values,
            child_lengths=child_lengths,
            lenghts=lengths)


class Tiler:
    def __init__(self, node, num_tiles=1, reduce2multiple=None):
        self.node = node
        self.num_tiles = num_tiles if hasattr(num_tiles, "__len__") else [num_tiles]
        self.reduce2multiple = reduce2multiple
        self.type = c.TYPE_PROC
