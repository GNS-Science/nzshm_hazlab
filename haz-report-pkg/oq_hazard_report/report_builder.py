from dataclasses import dataclass
from imp import load_dynamic
from socket import inet_aton
from sre_constants import IN
import numpy as np
from pathlib import PurePath, Path
from unittest import result
import matplotlib.pyplot as plt
import markdown
from markdown.extensions.toc import TocExtension
import os

from zipfile import ZipFile

import oq_hazard_report.read_oq_hdf5
import oq_hazard_report.plotting_functions
import oq_hazard_report.prepare_design_intensities
import oq_hazard_report.read_oq_hazstore

from oq_hazard_report.resources.css_template import css_file

HEAD_HTML = '''
<!DOCTYPE html>
<html>
<head>
<title>##TITLE##</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="hazard_report.css">
<style>
    .markdown-body {
        box-sizing: border-box;
        min-width: 200px;
        max-width: 1000px;
        margin: 0 auto;
        padding: 45px;
    }

    @media (max-width: 767px) {
        .markdown-body {
            padding: 15px;
        }
    }
</style>
</head>
<article class="markdown-body">

'''

TAIL_HTML = '''
</article>
</html>

'''

MAX_ROW_WIDTH = 2
POES = [0.1,0.02]
RPS = [25,50]
PLOT_WIDTH = 12
PLOT_HEIGHT = 8.625
INVESTIGATION_TIME = 50
IMTS = ['PGA','SA(0.5)','SA(1.0)','SA(1.5)','SA(2.0)',
        'SD(0.5)','SD(1.0)','SD(1.5)','SD(2.0)']
SITES = ['Auckland','Blenheim']

class ReportBuilder:

    #TODO
        # - in addition to a zip archive accept a directory or hdf5 
        # - currently assume only 1 hdf5 file in the zip, what happens if there are multiple?
        # -  some error handling for inputs (do the list of strings match the options?)

    def __init__(self,name='', plot_types=['hcurve'], hazard_archive=None, output_path=None):
        self._name = name
        self._hazard_archive = hazard_archive
        self._output_path = output_path
        self._plot_types = plot_types

    def setName(self,name):
        self._name = name
    
    def setHazardArchive(self,archive):
        self._hazard_archive = archive
        self._use_hdf5 = True

    def setHazardStore(self,hazard_id):
        self._hazard_id = hazard_id
        self._use_hdf5 = False

    def setOutputPath(self,output_path):
        self._output_path = output_path

    def setPlotTypes(self,plot_types):
        self._plot_types = plot_types

    def load_data(self):
        if self._use_hdf5:
            self.load_data_from_hdf5()
        else:
            self.load_data_from_hazstore()

    def load_data_from_hazstore(self):
        self.data = oq_hazard_report.read_oq_hazstore.retrieve_data(self._hazard_id)

    def load_data_from_hdf5(self):
        
        print('extracting archive . . .')
        with ZipFile(self._hazard_archive,'r') as zip:
            for n in zip.namelist():
                if 'calc' in n:
                    self.hdf_file = zip.extract(n,path=self._output_path)
        print('done extracting archive')

        self.data = oq_hazard_report.read_oq_hdf5.retrieve_data(self.hdf_file)
        os.remove(self.hdf_file)

    def run(self):

        #TODO optional args to specify which plots to generate

        self._plot_dir = Path(self._output_path,'figures')
        if not self._plot_dir.is_dir():
            self._plot_dir.mkdir()


        if not(self._output_path):
            raise Exception("output path must be specified")
        

        self.load_data()
        
        plots = []
        plots += self.generate_plots()

        self.generate_report(plots)



    def make_hazard_plots(self, args):

        intensity_type = args['intensity_type']

        xlim_log = args.pop('xlim_log',None)
        xlim = args.pop('xlim',None)

        args_linear = args.copy()
        args_linear['xlim'] = xlim
        args_linear['xscale'] = 'linear'
        args_log = args.copy()
        args_log['xlim'] = xlim_log
        args_log['xscale'] = 'log'

        # loop over sites and imts
        plots = []
        print('generating plots . . .')
        for site in self.data['metadata']['sites']['custom_site_id'].keys():

            # if site not in SITES: continue

            site_ = site.replace(' ','_')

            plots.append( dict(
                        level=3,
                        text=site,
                        fig_table = {}))

            figs_linear = [[]]
            titles_linear = [[]]
            figs_log = [[]]
            titles_log = [[]]
            col = 0
            row = 0
            for imt in self.data['metadata'][f'{intensity_type}_imtls'].keys():

                if imt not in IMTS: continue

                if col >= MAX_ROW_WIDTH:
                    col = 0
                    row += 1
                    figs_linear.append([])
                    titles_linear.append([])
                    figs_log.append([])
                    titles_log.append([])

                #------ linear ------#
                plot_path = PurePath(self._plot_dir,f'hcurve_{site_}_{imt}.png')
                plot_rel_path = PurePath(plot_path.parent.name,plot_path.name)
                print('writing',plot_rel_path)

                fig, ax = plt.subplots(1,1)
                fig.set_size_inches(PLOT_WIDTH,PLOT_HEIGHT)
                
                oq_hazard_report.plotting_functions.plot_hazard_curve(ax=ax, site_list=[site,], imt=imt,results=self.data, **args_linear)
                plt.savefig(str(plot_path), bbox_inches="tight")
                plt.close(fig)

                figs_linear[row].append(plot_rel_path)
                titles_linear[row].append(imt)
                
                #------ log ------#
                plot_path = PurePath(self._plot_dir,f'hcurve_{site_}_{imt}_log.png')
                plot_rel_path = PurePath(plot_path.parent.name,plot_path.name)
                print('writing',plot_rel_path)

                fig, ax = plt.subplots(1,1)
                fig.set_size_inches(PLOT_WIDTH,PLOT_HEIGHT)
                
                oq_hazard_report.plotting_functions.plot_hazard_curve(ax=ax, site_list=[site,], imt=imt,results=self.data,**args_log)
                plt.savefig(str(plot_path), bbox_inches="tight")
                plt.close(fig)

                figs_log[row].append(plot_rel_path)
                titles_log[row].append(imt)

                col += 1

                

            plots.append( dict(
                        level=4,
                        text='',
                        fig_table = {'figs':figs_linear, 'titles':titles_linear}))

            plots.append( dict(
                        level=4,
                        text='',
                        fig_table = {'figs':figs_log, 'titles':titles_log}))

        return plots


    def make_spectra_plots(self, rps, args):

        intensity_type = args['intensity_type']

        # loop over sites and imts
        print('generating plots . . .')
        plots = []
        for site in self.data['metadata']['sites']['custom_site_id'].keys():

            # if site not in SITES: continue

            figs = [[]]
            titles = [[]]
            col = 0
            row = 0
            for rp in rps:

                poe = 1-np.exp(-INVESTIGATION_TIME/rp)

                if col >= MAX_ROW_WIDTH:
                    col = 0
                    row += 1
                    figs.append([])
                    titles.append([])

                site_ = site.replace(' ','_')
                plot_path = PurePath(self._plot_dir,f'uhs_{site_}_{poe*100:.0f}_in_{INVESTIGATION_TIME:.0f}_{intensity_type}.png')
                plot_rel_path = PurePath(plot_path.parent.name,plot_path.name)
                print('writing',plot_rel_path)

                fig, ax = plt.subplots(1,1)
                fig.set_size_inches(PLOT_WIDTH,PLOT_HEIGHT)
                
                oq_hazard_report.plotting_functions.plot_spectrum(ax=ax, rp=rp, site=site,results=self.data, **args)
                plt.savefig(str(plot_path), bbox_inches="tight")
                figs[row].append(plot_rel_path)
                titles[row].append(f'{poe*100:.0f}% in {INVESTIGATION_TIME:.0f} years (1/{rp:.0f})')
                col += 1

                plt.close(fig)

            plots.append( dict(
                        level=3,
                        text=site,
                        fig_table = {'figs':figs, 'titles':titles})
            )

        return plots

    
    def generate_plots(self):

        plots = []


        if 'hcurve' in self._plot_types:

            ref_lines = []
            for poe in POES:
                ref_line = dict(type = 'poe',
                                poe = poe,
                                inv_time = INVESTIGATION_TIME)
                ref_lines.append(ref_line)
            for rp in RPS:
                ref_line = dict(type='rp',
                                rp=rp,
                                inv_time=INVESTIGATION_TIME)
                ref_lines.append(ref_line)

            xlim = [0,5]
            xlim_log = [1e-2,1e1]
            ylim = [1e-6,1]

            args = dict(
                ref_lines=ref_lines,
                xlim=xlim,
                xlim_log=xlim_log,
                ylim=ylim,
                quant=True,
                mean=True,
                legend_type='quant',
                intensity_type='acc'
            )

            plots.append( dict(
                    level=1,
                    text='Hazard Curves',
                    figs=[])
                )

            print('hazard curves . . .')
            plots += self.make_hazard_plots(args)
            print('done with hazard curves')

        if 'uhs' in self._plot_types:

            plots.append( dict(
                    level=1,
                    text='Spectra',
                    figs=[])
                )

            rps = np.concatenate( (RPS, -INVESTIGATION_TIME/np.log(1 - np.array(POES))) )

            intensity_type = 'acc'
            im_hazard, stats_im_hazard = oq_hazard_report.prepare_design_intensities.calculate_hazard_design_intensities(self.data,rps,intensity_type)
            self.data['hazard_design'] = {intensity_type:dict()}

            self.data['hazard_design'][intensity_type]['im_hazard'] = im_hazard
            self.data['hazard_design'][intensity_type]['stats_im_hazard'] = stats_im_hazard
            self.data['hazard_design']['hazard_rps'] = rps

            args = dict(
                inv_time=INVESTIGATION_TIME,
                mean=True,
                quant=True,
                legend_type='quant',
                intensity_type=intensity_type
            )

            plots.append( dict(
                    level=2,
                    text='Acceleration',
                    figs=[])
                )

            plots += self.make_spectra_plots(rps,args)

            intensity_type = 'disp'
            im_hazard, stats_im_hazard = oq_hazard_report.prepare_design_intensities.calculate_hazard_design_intensities(self.data,rps,intensity_type)
            self.data['hazard_design'] = {intensity_type:dict()}

            self.data['hazard_design'][intensity_type]['im_hazard'] = im_hazard
            self.data['hazard_design'][intensity_type]['stats_im_hazard'] = stats_im_hazard
            self.data['hazard_design']['hazard_rps'] = rps


            args = dict(
                inv_time=INVESTIGATION_TIME,
                mean=True,
                quant=True,
                legend_type='quant',
                intensity_type=intensity_type
            )

            plots.append( dict(
                    level=2,
                    text='Displacement',
                    figs=[])
                )

            print('spectra . . . ')
            plots += self.make_spectra_plots(rps,args)
            print('done with spectra')

        if 'dissags' in self._plot_types:
            args = dict()


        return plots


    def generate_report(self,plots):

        print('generating report . . .')

        md_string = f'# {self._name}\n'
        md_string += '<a name="top"></a>\n'
        md_string += '\n'
        md_string += '[TOC]\n'
        md_string += '\n'

        for plot in plots:
            md_string += f'{"#"*(plot["level"]+1)} {plot["text"]}\n'
            if plot['level'] < 4:
                md_string += f'[top](#top)\n'
            if plot.get('fig'):
                md_string += f'<a href={plot["fig"]} target="_blank">![an image]({plot["fig"]})</a>\n'
            if plot.get('fig_table'):
                md_string += self.build_fig_table(plot.get('fig_table'))

    
        html = markdown.markdown(md_string, extensions=[TocExtension(toc_depth="2-4"),'tables'])

        head_html = HEAD_HTML.replace('##TITLE##',self._name)
        html = head_html + html + TAIL_HTML        
        
        with open(PurePath(self._output_path, 'index.html'),'w') as output_file:
            output_file.write(html)

        with open(PurePath(self._output_path, 'hazard_report.css'),'w') as output_file:
            output_file.write(css_file)

        print('done generating report')


    def build_fig_table(self,fig_table):

        #TODO error handling for titles and figs not same shape

        def end_row(table_md):
            return table_md[:-3] + '\n'
        
        def insert_header_break(table_md,ncols):
            for col in range(ncols):
                table_md += ': ------------- : | '
            return table_md

        figs = fig_table.get('figs')
        titles = fig_table.get('titles')

        nrows = len(figs)
        ncols = len(figs[0])
        ncols_header = ncols

        table_md = '\n'

        for row in range(nrows):
            ncols = len(figs[row])

            for col in range(ncols):
                table_md += f'{titles[row][col]} | '
                if ncols < ncols_header:
                    for i in range(ncols_header-ncols):
                        table_md += '. | '
            table_md = end_row(table_md)

            if row==0:
                table_md = insert_header_break(table_md,ncols)
                table_md = end_row(table_md)

            for col in range(ncols):
                fig = figs[row][col]
                table_md += f'<a href={fig} target="_blank">![an image]({fig})<a href={fig} target="_blank"> | '
                if ncols < ncols_header:
                    for i in range(ncols_header-ncols):
                        table_md += '. | '

            table_md = end_row(table_md)

        table_md += '\n'

        return table_md



if __name__ == "__main__":

    datadir = '/home/chrisdc/NSHM/DEV/nzshm_hazlab/examples/openquake_hdf5_archive-T3BlbnF1YWtlSGF6YXJkVGFzazoxMDIwMjA='

    report_builder = oq_hazard_report.report_builder.ReportBuilder(output_path="/tmp/hazard_reports")
    report_builder.setName('TEST')
    report_builder.setHazardArchive('/home/chrisdc/NSHM/DEV/nzshm_hazlab/examples/openquake_hdf5_archive-T3BlbnF1YWtlSGF6YXJkVGFzazoxMDIwMjA=.zip')

    

    