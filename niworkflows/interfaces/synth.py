from nipype.interfaces.base import (
    traits,
    BaseInterfaceInputSpec,
    TraitedSpec,
    File,
    SimpleInterface,
)
from nipype.interfaces.freesurfer.base import FSTraitedSpecOpenMP, FSCommandOpenMP
import os.path as op
import nibabel as nb
import shutil

def _copyxform(ref_image, out_image, message=None):
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

class _SynthStripInputSpec(FSTraitedSpecOpenMP):
    input_image = File(
        argstr="-i %s",
        exists=True,
        mandatory=True)
    no_csf = traits.Bool(
        argstr='--no-csf',
        desc="Exclude CSF from brain border.")
    border = traits.Int(
        argstr='-b %d',
        desc="Mask border threshold in mm. Default is 1.")
    gpu = traits.Bool(argstr="-g")
    out_brain = File(
        argstr="-o %s",
        name_template="%s_brain.nii.gz",
        name_source=["input_image"],
        keep_extension=False,
        desc="skull stripped image with corrupt sform")
    out_brain_mask = File(
        argstr="-m %s",
        name_template="%s_mask.nii.gz",
        name_source=["input_image"],
        keep_extension=False,
        desc="mask image with corrupt sform")


class _SynthStripOutputSpec(TraitedSpec):
    out_brain = File(exists=True)
    out_brain_mask = File(exists=True)


class SynthStrip(FSCommandOpenMP):
    input_spec = _SynthStripInputSpec
    output_spec = _SynthStripOutputSpec
    _cmd = "mri_synthstrip"

    def _num_threads_update(self):
        if self.inputs.num_threads:
            self.inputs.environ.update(
                {"OMP_NUM_THREADS": "1"}
            )


class FixHeaderSynthStrip(SynthStrip):

    def _run_interface(self, runtime, correct_return_codes=(0,)):
        # Run normally
        runtime = super(FixHeaderSynthStrip, self)._run_interface(
            runtime, correct_return_codes)

        outputs = self._list_outputs()
        if not op.exists(outputs["out_brain"]):
            raise Exception("mri_synthstrip failed!")

        if outputs.get("out_brain_mask"):
            _copyxform(
                self.inputs.input_image,
                outputs["out_brain_mask"])

        _copyxform(
            self.inputs.input_image,
            outputs["out_brain"])

        return runtime