from os import listdir, path, remove

import pickle as pkl

from garage.contrib.exp.checkpointer.checkpointer import Checkpointer
from garage.contrib.exp.checkpointer.checkpointer import get_now_timestamp
from garage.contrib.exp.checkpointer.checkpointer import get_timestamp
from garage.contrib.exp.checkpointer.checkpointer import cat_for_fname


class DiskCheckpointer(Checkpointer):
    def __init__(self, exp_dir, resume, prefix):
        super(DiskCheckpointer, self).__init__(resume, prefix)
        self.exp_dir = exp_dir

    def load(self, **kwargs):
        """Load checkpoint from disk if there exists.

        Load checkpoint from exp_dir directory.

        If there's no saved checkpoint, create an initial checkpoint instead.
        This usually happens when an experiment is run for the first time
        and the initial states will be saved.

        A checkpoints might consist of several files, each is named
        in the format of [prefix_]timestamp_object.pkl and corresponds
        to a named argument.

        Args:
            **kwargs: Objects to save.
                The name of argument is used to name checkpoint file.

        Returns:
            dict: restored objects from disk.

        """
        latest_checkpoint = self._get_latest_checkpoint(kwargs.keys(), dry=True)
        if not latest_checkpoint or not self.resume:
            self.save(**kwargs)
            return kwargs
        else:
            return self._load(**kwargs)

    def save(self, **kwargs):
        """Save a new checkpoint to disk.

        Args:
            **kwargs: Objects to save.
                The name of argument is used to name checkpoint file.

        """
        timestamp = get_now_timestamp()

        for name, obj in kwargs.items():
            filename = cat_for_fname(self.exp_dir, timestamp, name)
            pkl.dump(obj, open(filename, 'wb'))

        self._clean_outdated(timestamp)

    def _load(self, **kwargs):
        """Load checkpoint from disk.

        Args:
            **kwargs: Objects to save.
                The name of argument is used to name checkpoint file.

        Returns:

        """
        return self._get_latest_checkpoint(kwargs.keys(), dry=False)

    def _is_valid_name(self, filename):
        """Test if name is valid saved object filename.

        Args:
            filename: filename to test.

        Returns:
            bool: if name is valid saved object filename.
        """
        segs = filename.split('_')

        if len(segs) < 2 + bool(self.prefix):
            return False

        segs[-1], subfix = segs[-1].split('.')
        if subfix != 'pkl':
            return False

        if self.prefix:
            if segs[0] != self.exp_dir:
                return False;
            if not get_timestamp(segs[1]):
                return False
        else:
            if not get_timestamp(segs[0]):
                return False

        return True

    def _get_saved_names(self):
        """Get all valid saved object filenames under exp_dir.

        Returns:
            list: list of valid saved object filenames.

        """
        return [path.join(self.exp_dir, f) for f in listdir(self.exp_dir) if self._is_valid_name(f)]

    def _get_latest_checkpoint(self, obj_names, dry=False):
        """Get latest valid checkpoint.

        Returns:
            dict: Latest valid checkpoint.

        """
        ret_cp = {}
        latest_timestamp = ""

        saved_names = self._get_saved_names()
        timestamps = set([get_timestamp(name) for name in saved_names])

        for timestamp in timestamps:
            cp = {}
            files = [file for file in saved_names if timestamp in file]

            for obj_name in obj_names:
                for file in files:
                    if obj_name in file:
                        cp['obj_name'] = pkl.load(open(file, 'rb')) if not dry else ""

            if len(cp) == len(obj_names) and timestamp > latest_timestamp:
                ret_cp = cp

        return ret_cp

    def _clean_outdated(self, latest_timestamp):
        """Remove checkpoints other than latest_timestamp.

        Args:
            latest_timestamp: timestamp to exclude.

        """
        files = self._get_saved_names()
        for file in files:
            if latest_timestamp not in files:
                remove(file)
