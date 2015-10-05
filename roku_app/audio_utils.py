# -*- coding: utf-8 -*-
"""
Audio utilities for RokuApp

Created on Fri Jun 19 17:08:47 2015

@author: ddboline
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os

from .util import run_command
from .roku_utils import HOMEDIR, get_length_of_mpg


def make_audio_analysis_plots(infile, prefix='temp', make_plots=True,
                              do_fft=True, fft_sum=None):
    ''' create frequency plot '''
    import numpy as np
    from scipy import fftpack
    from scipy.io import wavfile
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as pl

    if not os.path.exists(infile):
        return -1

    try:
        rate, data = wavfile.read(infile)
    except ValueError:
        print('error reading wav file')
        return -1
    dt_ = 1./rate
    time_ = dt_ * data.shape[0]
    tvec = np.arange(0, time_, dt_)
    sig0 = data[:, 0]
    sig1 = data[:, 1]
    if not tvec.shape == sig0.shape == sig1.shape:
        return -1
    if not do_fft:
        fft_sum_ = float(np.sum(np.abs(sig0)))
        if hasattr(fft_sum, 'value'):
            fft_sum.value = fft_sum_
        return fft_sum_
    if make_plots:
        pl.clf()
        pl.plot(tvec, sig0)
        pl.plot(tvec, sig1)
        xtickarray = range(0, 12, 2)
        pl.xticks(xtickarray, ['%d s' % x for x in xtickarray])
        pl.savefig('%s/%s_time.png' % (HOMEDIR, prefix))
        pl.clf()
    samp_freq0 = fftpack.fftfreq(sig0.size, d=dt_)
    sig_fft0 = fftpack.fft(sig0)
    samp_freq1 = fftpack.fftfreq(sig1.size, d=dt_)
    sig_fft1 = fftpack.fft(sig1)
    if make_plots:
        pl.clf()
        pl.plot(np.log(np.abs(samp_freq0)+1e-9), np.abs(sig_fft0))
        pl.plot(np.log(np.abs(samp_freq1)+1e-9), np.abs(sig_fft1))
        pl.xlim(np.log(10), np.log(40e3))
        xtickarray = np.log(np.array([20, 1e2, 3e2, 1e3, 3e3, 10e3, 30e3]))
        pl.xticks(xtickarray, ['20Hz', '100Hz', '300Hz', '1kHz', '3kHz',
                               '10kHz', '30kHz'])
        pl.savefig('%s/%s_fft.png' % (HOMEDIR, prefix))
        pl.clf()

        run_command('mv %s/%s_time.png %s/%s_fft.png %s/public_html/videos/'
                    % (HOMEDIR, prefix, HOMEDIR, prefix, HOMEDIR))

    fft_sum_ = float(np.sum(np.abs(sig_fft0)))
    if hasattr(fft_sum, 'value'):
        fft_sum.value = fft_sum_
    return fft_sum_


def make_time_series_plot(input_file='', prefix='temp'):
    ''' create wav and time plot '''
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as pl

    length_of_file = get_length_of_mpg(input_file)
    audio_vals = []
    for time_ in range(0, length_of_file, 60):
        run_command('mpv --start=%d ' % time_ +
                    '--length=10 --ao=pcm:fast:file=%s/' % HOMEDIR +
                    '%s.wav --no-video ' % prefix +
                    '%s 2> /dev/null > /dev/null' % input_file)
        aud_int = make_audio_analysis_plots('%s/%s.wav' % (HOMEDIR, prefix),
                                            make_plots=False, do_fft=False)
        audio_vals.append(aud_int)
    #print(audio_vals)
    x__ = np.arange(0, length_of_file, 60)
    y__ = np.array(audio_vals)
    pl.clf()
    pl.plot(x__/60., y__)
    pl.savefig('%s/%s_time.png' % (HOMEDIR, prefix))
    pl.clf()
    run_command('mv %s/%s_time.png %s/public_html/videos/' % (HOMEDIR, prefix,
                                                              HOMEDIR))
    return 'Done'
