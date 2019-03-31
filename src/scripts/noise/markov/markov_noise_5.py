print('IMPORTING MODULES')
import time
import numpy as np
import constants as c
import utils.generate_utils as gen
import utils.file_utils as file
import utils.data_utils as data
import utils.markov_utils as m
import utils.color_utils as color
import utils.viz_utils as viz

### DATA/INPUT/SHARED by all runs section
print('PREPARING DATA SECTION')

N = 2

HEIGHT = 100
WIDTH  = HEIGHT

TILE_WIDTH = 10
TILE_HEIGHT = TILE_WIDTH

UPSCALE_FACTOR = c.INSTA_SIZE // HEIGHT

TILING_OPTIONS = [1,2,3,4,5]

SCHEME_COLORS = {
    1: color.hex2arr('ffe62b'),
    2: color.hex2arr('ff4f14'),
    3: color.hex2arr('ea0042'),
    4: color.hex2arr('195ed6'),
    5: color.hex2arr('7c13c6'),
}

COLOR_DICT = {
    0: color.hex2arr('030026'),

    **SCHEME_COLORS
}

print(COLOR_DICT)

### SETUP section
print('SETUP SECTION')
file.clear_export_dir()


### FUNCTIONS section
print('FUNCTIONS SETUP')


line = np.ones((UPSCALE_FACTOR,UPSCALE_FACTOR))
line[:,[0,1,2,3]] = 0
line[:,[UPSCALE_FACTOR-1,UPSCALE_FACTOR-2,UPSCALE_FACTOR-3,UPSCALE_FACTOR-4]] = 0
print(line)


def gen_channel(parent):
    img = m.paint_linearly_markov_hierarchy(
        markov_tree=parent,
        width=WIDTH, height=HEIGHT,
        tile_height=TILE_HEIGHT,tile_width=TILE_WIDTH)
    img = data.upscale_nearest(img,UPSCALE_FACTOR)
    # img = data.upscale_with_circle(img,UPSCALE_FACTOR,bg=0)
    # img = data.upscale_with_shape(img,line,bg=0)
    return img.reshape(img.shape[0],img.shape[1],1)

def gen_patterns(bg,min_bg,l,others):
    base = np.ones(l,dtype='int8')*bg

    a = np.random.choice(len(others))
    b = (a+1)%len(others)
    a = others[a]
    b = others[b]

    num_as = np.random.choice(l-min_bg)
    num_bs = np.random.choice(l-num_as-min_bg)

    print(a,b,num_as,num_bs)

    poss = np.random.choice(l,size=(num_as+num_bs),replace=False)
    pos_a = poss[:num_as]
    pos_b = poss[num_as:]

    base[pos_a] = a
    base[pos_b] = b

    return ''.join([str(i) for i in base])

def clean_pattern(s):
    return s.replace('-','')

def gen_all_possible_permutations(pattern,others):
    pattern = clean_pattern(pattern)
    t = [int(i) for i in pattern]

    cart_product = []
    for i in others:
        for j in others:
            for k in others:
                if i!=j and i!= k and k!=i:
                    cart_product += [(i,j,k)]

    all_perms = set()
    for p in cart_product:
        s = ''.join( p[i] for i in t )
        all_perms.add(s)

    return list(all_perms)



### GENERATE SECTION
print('GENERATE SECTION')

for current_iteration in range(N):

    np.random.seed(10+current_iteration)

    combinations = [np.random.choice(5,size=(2,))+1 for i in range(20)]
    basic_tiles = []
    for a,b in combinations:

        # pats = [
        #     gen_all_possible_permutations('00000',['0','1','2']),
        #     gen_all_possible_permutations('10001',['0','1','2']),
        #     gen_all_possible_permutations('10101',['0','1','2']),
        #     gen_all_possible_permutations('10201',['0','1','2']),
        #     gen_all_possible_permutations('02120',['0','1','2']),
        #     gen_all_possible_permutations('00100',['0','1','2']),
        # ]

        pats = [
            #                              12--|-|--21
            gen_all_possible_permutations('00000-00000',['0','1','2']),
            gen_all_possible_permutations('00001-10000',['0','1','2']),
            gen_all_possible_permutations('00011-11000',['0','1','2']),
            gen_all_possible_permutations('00111-11100',['0','1','2']),
            gen_all_possible_permutations('01111-11110',['0','1','2']),

            gen_all_possible_permutations('01222-22210',['0','1','2']),
            gen_all_possible_permutations('01122-22110',['0','1','2']),
            gen_all_possible_permutations('00112-21100',['0','1','2']),

            gen_all_possible_permutations('01100-00110',['0','1','2']),
            gen_all_possible_permutations('11000-00011',['0','1','2']),
            gen_all_possible_permutations('01000-00010',['0','1','2']),
            gen_all_possible_permutations('00010-01000',['0','1','2']),
            gen_all_possible_permutations('00100-00100',['0','1','2']),
            gen_all_possible_permutations('01101-10110',['0','1','2']),
            gen_all_possible_permutations('01110-01110',['0','1','2']),
            gen_all_possible_permutations('01210-01210',['0','1','2']),

            gen_all_possible_permutations('00000-10001',['0','1','2']),
            gen_all_possible_permutations('10001-00000',['0','1','2']),
            gen_all_possible_permutations('01010-00000',['0','1','2']),
            gen_all_possible_permutations('00000-01010',['0','1','2']),
        ]

        pats = [j for i in pats for j in i]
        # print(pats)

        pats = [
            m.SimpleProgression(
                values=m.SimplePattern(pattern=i,candidates=[0]+[int(a),int(b)],start_probs=0   ),
                child_lengths=TILE_WIDTH)
            for i in pats
        ]

        pats = m.Tiler(
            m.SimpleProgression(
                values=m.RandomMarkovModel(values=pats,child_lengths=1),
                child_lengths=TILE_HEIGHT),
            num_tiles=TILING_OPTIONS)

        basic_tiles += [pats]

    parent = m.RandomMarkovModel(
        values=basic_tiles,
        child_lengths=1)


    s = current_iteration*10
    img = gen_channel(parent)[:,:,0]
    print(img.shape)
    print(np.min(img))
    print(np.max(img))
    colored_image = color.replace_indices_with_colors(img, COLOR_DICT)
    print(colored_image.shape)

    if N==1:
        viz.show_image(colored_image)
    else:

        file.export_image(
            '%d_%d' % (current_iteration,int(round(time.time() * 1000))),
            colored_image.astype('uint8'),format='png')