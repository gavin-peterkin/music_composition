# J.S. Bot

The purpose of this project is to train a recurrent neural network (RNN) using scraped
midi files which fall under the creative commons license. Specifically, I'll be
using a long short term memory (LSTM) RNN to try to recreate improvised
Classical, Baroque, and Romantic musical styles. Ironically, J.S. Bot has not been trained
on any Bach--at least not yet.

_This project is still a work in progress..._

**For some audio samples visit my blog [here](http://gavin-peterkin.github.io/science/2017/09/13/j_s_bot.html).**

## Business Understanding

Some existing algorithmic music composition procedures are limited in that they try
to adapt networks designed for text prediction for music prediction. In many cases,
this means that the network can only capture a monophonic melody and is incapable
of learning harmonic relationships, which play a huge role in our perception and
appreciation of music.

These are some of the goals I hope to achieve with this project:
* The network is capable of playing multiple notes
* The network can use chord progressions and melodic fragments together
* The network operates in a single key signature unless it momentarily uses modulation
for musical effect
* A musical style can be determined from synthesized output
* Can we learn new things about a composer or style by examining a RNN model?

A network that met some of these criteria could have tons of applications. It could be used to generate
a never-ending streaming radio station trained on a user's favorite musical styles or artists.
It could also be used during live performances where the performer's actions are
fed to the model and the network's next step prediction is played along with the
performer's. This would make a nice automatic accompaniment or "duet" program.
Finally, it could be used an aid to the composition process.

## Data Understanding and Preparation

### Scraping and Download
Training data were collected from [IMSLP](http://imslp.org). I used the library
[Scrapy](https://scrapy.org) to construct a spider to walk through web pages and
collect midi files and their associated meta data as they were found. Some advantages
to using Scrapy is that it's incredibly easy to extend a spider to traverse another
section of the website, which I may do later in order to grow my local midi file database.
The spider code is located here: [src/scraping/midi](src/scraping/midi)

Metadata collected by the spider were stored in a local MongoDB. The next step in
the process was the download of the midi files and storage onto an Amazon Web Services
(AWS) S3 bucket.

### Parsing
Since the midi file format is incredibly complicated and outdated (see
[the format spec](http://www.music.mcgill.ca/~ich/classes/mumt306/StandardMIDIfileformat.html)),
I used the python library [mido](https://mido.readthedocs.io/en/latest/) to access
the midi meta messages and tracks. I discovered that many of the files had multiple
tracks that needed to be merged despite being "piano pieces". I decided to use the
16th note as the smallest unit of musical information. Throughout the code, a "beat"
usually means a 16th note.

I also store some additional meta data in the files in the database--things like key
signature specifically. The intermediate form of the music was then transformed into what
is referred to throughout the code as a "list_of_notes". More descriptively, it's a
relatively easy-to-read format that's a list of lists. The inner lists are each one beat
and they contain tuples of notes (integers from 0 to 128) and a character "b" or "s"
indicating whether or not this is the beginning of the note or if it's being sustained
from a previous hit. I'm not currently modeling note sustains.

The `InputLayerExtractor` prepares a list of notes object for network training.
First, it transposes the music from it's original key into C major or A minor.
The network is trained on major and minor pieces. I made this design decision because
it's relatively easy to transpose music after the fact. Classical and especially popular
music spend most time in only one key, which is why it's important
for the network to also be trained in only one key in order for it to learn proper
harmonic relationships.

A single input layer vector consists of 128 floats that indicate
which notes are being played in the beat and 10 floats indicating the number of notes
to play during this beat. The number of notes one-hot-encoding is then used
together with the predicted note probabilities to select the x most likely notes.

See [`src/parsing/`](src/parsing/) to review the code.

![png](/graphics/data_pipeline.png)

## Modeling
The processed data is stored as a binary arrays in the MongoDB, so it's easily accessible
for training via a series of generators (a lazily-evaluating iterator in python).
I did this to prevent training from becoming memory-bound in any way.

During training, a section of a piece is returned based on a truncated lookback parameter.
I found that about two measures or 128 16th notes seemed to be enough for some changing,
if perhaps a bit repetitive, harmonic progressions.

The most challenging component of the modeling process has been figuring out how
to mitigate the song overfitting issue. Loss (defined as [categorical crossentropy](https://en.wikipedia.org/wiki/Cross_entropy)) seems to have distinct minima for
different songs. Pieces that exhibit musical differences, like Baroque and Modern
for example, are then extremely difficult to fit simultaneously.

I attempted to address this problem in a few ways. First, I limited training samples
to a single distinct musical style either by using the works of only a single composer
or a composer time period. I also made some adjustments to the network architecture.
I used a fairly large dropout at two points in the network. I also injected Gaussian
noise with a somewhat high standard deviation into the input layer. These techniques
_may_ have helped some, but the network was still clearly fitting to local song minima
rather than "musical theory" minima, which to some extent was to be expected.

### A simplified network diagram
![png](/graphics/network.png)

* The input and output size of one timestep is 138
* The input layer was adjusted by introducing gaussian noise during training
* The number of hidden dimensions was freely adjusted from 200 to about 500
* The first LSTM layer returned sequences
* A dropout of around 0.4 was used for each LSTM layer
* This diagram omits the time dimension for clarity


## Music Synthesis
In order to avoid translating my results back into midi for playback, I created
my own Playback class which takes a `list_of_notes` object and can either play the mono stream
through output or save it to a wav file. All of the musical samples were created
using Playback in the [utility directory](/src/utility/).

An additional benefit of this approach is that I get to define my own oscillators,
so I can add whichever harmonics I want and not be limited to some of the worse-sounding
midi instruments.

## Evaluation

Survey results indicate that users prefer network-generated output to "random" music.
Users can also distinguish model output from actual music composed by humans.
![png](/graphics/response_hist.png)

## Areas for Improvement

* **More accurate reporting** of overfitting by analyzing loss on an out-of-sample
collection of similar compositions.

* **Control overfitting** possibly by decreasing the learning rate and increasing
the number of epochs.
In some instances the network is probably overfitting. Rather than fitting some
general style, it's fitting the very specific style of a single piece. This was reflected
during training when the loss would decrease steadily until the network was exposed
to something new and jumped back up again. There may also be ways of mitigating
with some additional transformation of the training data.

* **Cluster music** Since there's such a large quantity of music out there,
it may make sense to cluster music first into distinct categories and _then_
train models on that distinct genre.

* **Parameter tuning** There are a lot of parameters that need to be tuned. It's
not easy to test new hyperparameters since a training session can be unsuccessful
for a _very_ long time even if it is slowly converging on an optima. The easiest
way to confront this problem would be to use more computer power.

* **More data** As always, more data would definitely help improve the model and
ameliorate the overfitting problem.

* **More compute power** By moving training on to an AWS EC2 instance with much
better graphics specs, I could drastically reduce the training time.

## Thoughts for future development

* **Combine models** by having them synthesize collaboratively. Using several models
trained in different styles, it should be possible to have them each independently
make predictions which are then combined to inform each model's next prediction.
A piece generated in this way could have many different voices--like most human
music.

## General Usage Notes

### Some requirements
You'll need to have MongoDB installed and running in order for scraping to work.
The download pipeline also assumes you have a AWS credentials set up and a midi bucket.
I can make my bucket of midi files public if there's interest...

I used a virtualenv for this project with Python 2.7. In order to recreate or adapt this work
for your own purposes, clone the repo and in a new virtualenv run:

`pip install -r requirements.txt` (obtained via `pip freeze > requirements.txt`)

Additionally, run the following to add the project to your python path:

`add2virtualenv <absolute path to src dir>`


## Resources

I made extensive use of online resources for this project. I don't think I wouldn't
have gotten far without extensive use of the following resources.

### Coding

* [How to build a RNN in TensorFlow](https://medium.com/@erikhallstrm/hello-world-rnn-83cd7105b767)

* [LSTM by Example using Tensorflow](https://medium.com/towards-data-science/lstm-by-example-using-tensorflow-feb0c1968537)

* [A repo for jazz synthesis with Keras](https://github.com/jisungk/deepjazz)

* [A music synthesis repo with Keras](https://github.com/MattVitelli/GRUV)

* [TensorFlow Cookbook](https://github.com/nfmcclure/tensorflow_cookbook#ch-9-recurrent-neural-networks)

### Neural Network Background and Theory

* [Understanding LSTMs Blog Post](http://colah.github.io/posts/2015-08-Understanding-LSTMs/)

* [The Unreasonable Effectiveness of RNNs](http://karpathy.github.io/2015/05/21/rnn-effectiveness/)

* [Dropout: A Simple Way to Prevent Overfitting](http://www.jmlr.org/papers/volume15/srivastava14a/srivastava14a.pdf)

* [Optimization Algorithms](http://ruder.io/optimizing-gradient-descent/index.html#rmsprop)

### Graphics

* [Neural Network texample.net](http://www.texample.net/tikz/examples/neural-network/)

* [Flow Chart texample.net](http://www.texample.net/tikz/examples/simple-flow-chart/)
