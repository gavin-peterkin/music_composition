# Classical Music AI

The purpose of this project is to train a recurrent neural network (RNN) using scraped
midi files which fall under the creative commons license. Specifically, I'll be
using a long short term memory (LSTM) RNN to try to recreate improvised
Classical, Baroque, and Romantic musical styles.

_This project is still a work in progress..._

## Business Understanding

Some existing algorithmic music composition procedures are limited in that they try
to adapt networks designed for text prediction for music prediction. In many cases,
this means that the network can only capture a monophonic melody and is incapable
of learning harmonic relationships, which play a huge role in our perception and
appreciation of music.

These are some of the goals I hope to achieve with this project:
* The network is capable of playing multiple notes
* The network can discover chord progressions and melodic fragments and use them
together
* The network operates in a single key signature unless it momentarily uses modulation
for musical effect
* A musical style can be determined from synthesized output

A network that met these criteria could have tons of applications. It could be used to generate
a never-ending streaming radio station trained on a user's favorite musical styles or artists.
It could also be used during live performances where the performer's actions are
fed to the model and the network's next step prediction is played along with the
performer's. This would make a nice automatic accompaniment or "duet" program.

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

See [`src/parsing/`](src/parsing/).

## Modeling
(diagram here?)


## Areas for Improvement

* **Control overfitting** possibly by decreasing the learning rate and increasing
the number of epochs.
In some instances the network is probably overfitting. Rather than fitting some
general style, it's fitting the very specific style of a single piece. This was reflected
during training when the loss would decrease steadily until the network was exposed
to something new and jumped back up again. There may also be ways of mitigating
with some transformation of the training data.

## Thoughts for future development

* **Combine models** by having them synthesize collaboratively. Using several models
trained in different styles, it should be possible to have them each independently
make predictions which are then combined to inform each model's next prediction.
A piece generated in this way could have many different voices--like most human
music.

## General Usage Notes

I used a virtualenv for this project. In order to recreate or adapt this work
for your own purposes, clone the repo and in a new virtualenv run:

`pip install -r requirements.txt` (obtained via `pip freeze > requirements.txt`)

Additionally, run the following to add the project to your python path:

`add2virtualenv <absolute path to src dir>`


## Resources

### Coding

* [How to build a RNN in TensorFlow](https://medium.com/@erikhallstrm/hello-world-rnn-83cd7105b767)

* [LSTM by Example using Tensorflow](https://medium.com/towards-data-science/lstm-by-example-using-tensorflow-feb0c1968537)

* [A repo for jazz synthesis with Keras](https://github.com/jisungk/deepjazz)

* [A music synthesis repo with Keras](https://github.com/MattVitelli/GRUV)

### Neural Network Background and Theory

* [Understanding LSTMs Blog Post](http://colah.github.io/posts/2015-08-Understanding-LSTMs/)
