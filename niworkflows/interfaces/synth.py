from nipype.interfaces.base import (
    traits,
    BaseInterfaceInputSpec,
    TraitedSpec,
    File,
    SimpleInterface,
)
from nipype.interfaces.freesurfer.base import FSTraitedSpecOpenMP, FSCommandOpenMP
from nipype.utils.filemanip import fname_presuffix
import os.path as op
import nibabel as nb
import numpy as np
import shutil
import os

class _SynthStripInputSpec(TraitedSpec):
    input_image = File(
        exists=True,
        mandatory=True)
    no_csf = traits.Bool(
        desc="Exclude CSF from brain border.",
        mandatory=False)
    border = traits.Int(
        desc="Mask border threshold in mm. Default is 1.",
        mandatory=False)
    gpu = traits.Bool(mandatory=False)


class _SynthStripOutputSpec(TraitedSpec):
    out_brain = File(exists=True)
    out_brain_mask = File(exists=True)


class SynthStrip(SimpleInterface):
    input_spec = _SynthStripInputSpec
    output_spec = _SynthStripOutputSpec

    def _run_interface(self, runtime):

        def copyxform(ref_image, out_image, message=None):
            # Read in reference and output
            # Use mmap=False because we will be overwriting the output image
            resampled = nb.load(out_image, mmap=False)
            orig = nb.load(ref_image)

            if not np.allclose(orig.affine, resampled.affine):
                print(
                    'Affines of input and reference images do not match, '
                    'FMRIPREP will set the reference image headers. '
                    'Please, check that the x-form matrices of the input dataset'
                    'are correct and manually verify the alignment of results.')

            # Copy xform infos
            qform, qform_code = orig.header.get_qform(coded=True)
            sform, sform_code = orig.header.get_sform(coded=True)
            header = resampled.header.copy()
            header.set_qform(qform, int(qform_code))
            header.set_sform(sform, int(sform_code))
            header['descrip'] = 'xform matrices modified by %s.' % (message or '(unknown)')

            newimg = resampled.__class__(resampled.get_fdata(), orig.affine, header)
            newimg.to_filename(out_image)
        print(str(self.inputs.input_image))
        #set base command
        base_cmd = "python /opt/freesurfer/python/scripts/mri_synthstrip "

        outbrain_fname = fname_presuffix(
            self.inputs.input_image, suffix='_skullstripped',
            use_ext=True, newpath=runtime.cwd)
        
        outmask_fname = fname_presuffix(
            self.inputs.input_image, suffix='_boldmask',
            use_ext=True, newpath=runtime.cwd)
        
        #set mandatory arguments
        mandatory_args = "-i {inimg} -o {outbrain} -m {outmask} ".format(
        inimg=self.inputs.input_image,
        outbrain=outbrain_fname,
        outmask=outmask_fname
        )

        #combine and run
        full_cmd = base_cmd + mandatory_args
        print(str(self.inputs.input_image))
        print(full_cmd)
        os.system("which python")
        os.system("which mri_synthstrip")
        os.system(full_cmd)

        #rewrite headers
        copyxform(self.inputs.input_image,
                  outbrain_fname)
        
        copyxform(self.inputs.input_image,
                  outmask_fname)

        1/0
        #store results
        self._results['out_brain'] = outbrain_fname
        self._results['out_brain_mask'] = outmask_fname
        return runtime