"""DEFINED ONLY: seven pure installed-SDK binding/materializer refusal models."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import supervise_build as s
spec=importlib.util.spec_from_file_location('installed_sdk_materializer',HERE.parent/'materializer-source/materialize.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def pin(path):return {'path':str(path),'bytes':10,'sha256':'a'*64}


def fixture():
    release={name:pin('/SYNTHETIC/'+name+'.json') for name in (
        'jdkExtraction','installedSdkInventory','installedSdkMetadata','installedSdkConsent','installedSdkAcceptance')}
    release['prerequisiteAcceptances']=[release['installedSdkAcceptance']]
    reference=copy.deepcopy(release);reference['installedSdkAcceptanceDecision']=s.SDK_DECISION
    installed={'destination':str(s.SDK),'inventory':[],'symlinkModes':[]}
    metadata={'sdkRoot':str(s.SDK),'packages':[
        {'package':package,'packageXml':pin(s.SDK/relative/'package.xml'),
         'sourceProperties':pin(s.SDK/relative/'source.properties')} for package,relative in s.SDK_PACKAGES.items()],
        'actualGeneratedLicenseFile':pin(s.SDK/'licenses/android-sdk-license'),
        'installationResult':pin('/SYNTHETIC/actual-installation-result.json')}
    consent={'schema':'nbdp-installed-sdk-consent-observation-v1','sdkRoot':str(s.SDK),
        'installation':pin('/SYNTHETIC/retained-installation-result.json'),'lifecycleAcceptance':pin('/SYNTHETIC/lifecycle.json'),
        'consumption':'UNKNOWN','consent':{'affirmativeAttempted':True,'attemptJournalCommitted':True,
            'stdinWriteInvoked':True,'writeReturnedBytes':2,'flushReturned':True,'sent':True,
            'sentJournalCommitted':True,'flushAndSentRecorded':True,'consumption':'UNKNOWN'}}
    accepted={'schema':'nbdp-installed-sdk-data-acceptance-v1','decision':s.SDK_DECISION,'sdkRoot':str(s.SDK),
        'inventory':release['installedSdkInventory'],'metadata':release['installedSdkMetadata'],
        'consent':release['installedSdkConsent'],'installationLifecycle':consent['lifecycleAcceptance'],
        'installationOrigin':metadata['installationResult'],'retainedInstallation':consent['installation']}
    return reference,release,accepted,installed,metadata,consent


class InstalledSdkBindings(unittest.TestCase):
    def test_exact_whole_sdk_root_and_acceptance_chain(self):
        values=fixture();self.assertEqual(len(s.installed_sdk_binding(*values)),3)

    def test_null_wrong_decision_or_old_root_is_refused(self):
        for mutate in (lambda x:x[0].update(installedSdkInventory=None),
                lambda x:x[2].update(decision='ACCEPT_RAW_ARCHIVES_ONLY'),
                lambda x:x[3].update(destination='/SYNTHETIC/old-sdk')):
            values=fixture();mutate(values)
            with self.assertRaises(ValueError):s.installed_sdk_binding(*values)

    def test_cross_subject_descriptor_or_missing_acceptance_refused(self):
        for mutate in (lambda x:x[2].update(metadata=pin('/FOREIGN/metadata.json')),
                lambda x:x[2].update(consent=pin('/FOREIGN/consent.json')),
                lambda x:x[1].update(prerequisiteAcceptances=[])):
            values=fixture();mutate(values)
            with self.assertRaises(ValueError):s.installed_sdk_binding(*values)

    def test_package_metadata_install_and_answer_facts_cannot_drift(self):
        for mutate in (lambda x:x[4]['packages'][0].update(package='platform-tools'),
                lambda x:x[4]['packages'][0].update(packageXml=pin('/FOREIGN/package.xml')),
                lambda x:x[5].update(installation=pin('/FOREIGN/installation.json')),
                lambda x:x[5]['consent'].update(writeReturnedBytes=True),
                lambda x:x[5]['consent'].update(sentJournalCommitted=False),
                lambda x:x[5].update(consumption='PROVEN')):
            values=fixture();mutate(values)
            with self.assertRaises(ValueError):s.installed_sdk_binding(*values)

    def test_materializer_exact_new_sdk_fields_are_valid_shapes(self):
        values=fixture();m.sdk_release_shape(values[1])

    def test_materializer_old_extractions_or_null_sdk_is_refused(self):
        for mutate in (lambda x:x.update(extractions={}),lambda x:x.update(installedSdkMetadata=None)):
            release=fixture()[1];mutate(release)
            with self.assertRaises(ValueError):m.sdk_release_shape(release)

    def test_materializer_requires_distinct_evidence_and_whole_acceptance(self):
        for mutate in (lambda x:x.update(prerequisiteAcceptances=[]),
                lambda x:x.update(installedSdkMetadata=x['installedSdkInventory'])):
            release=fixture()[1];mutate(release)
            with self.assertRaises(ValueError):m.sdk_release_shape(release)


if __name__=='__main__':unittest.main(verbosity=2)
