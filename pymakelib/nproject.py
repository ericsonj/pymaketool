from os import execle
import tarfile
import tempfile
import re
from pathlib import Path
from abc import ABC,abstractmethod
from prompt_toolkit import prompt
from prompt_toolkit.completion import PathCompleter, WordCompleter
from prompt_toolkit.validation import Validator
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from . import Logger

log = Logger.getLogger()

class Object(object):
    pass

class PromptUtil:

    def __init__(self) -> None:
        self.bindings = KeyBindings()
        
        @self.bindings.add(Keys.ControlC)
        def _(event):
            exit(0)

    def add_answers(self, answers: dict):
        self.answers = answers

    def parse_answers(self):
        obj = Object()
        for a in self.answers:
            type = a['type']
            name = a['name']
            self.answer = a
            res = getattr(self, type)()
            setattr(obj, name, res)
        return obj


    def __get_commond_attr(self):
        msg = self.answer['msg']
        default = '' if not "default" in self.answer else self.answer["default"]
        validator_dict = None if not "validator" in self.answer else self.answer["validator"]
        validator = None
        if validator_dict:
            validator = Validator.from_callable(
                validator_dict['callback'],
                error_message=validator_dict['error_msg'],
                move_cursor_to_end=True)
        return msg, default, validator


    def input(self):
        msg, default, validator = self.__get_commond_attr()
        return prompt(msg, default=default, validator=validator, key_bindings=self.bindings)


    def input_path(self):
        msg, default, validator = self.__get_commond_attr()
        path_completer = PathCompleter(only_directories=True, min_input_len=1)
        return prompt(msg, completer=path_completer, default=default, validator=validator, key_bindings=self.bindings)


    def confirm(self):
        msg, default, validator = self.__get_commond_attr()
        word_completer = WordCompleter(["yes", "no"])
        resp = prompt(msg, completer=word_completer, default=default, validator=validator, key_bindings=self.bindings)
        return True if resp == 'yes' or resp == 'y' else False



class AbstractGenerator(ABC):

    @abstractmethod
    def info(self) -> dict:
        pass

    @abstractmethod
    def exec_generator(self, **kwargs):
        pass


class BasicGenerator(AbstractGenerator):

    @abstractmethod
    def get_attrs(self, **kwargs) -> dict:
        pass


    def parse_args(self, args:list) -> dict:
        res = []
        for sub in args:
            if '=' in sub:
                res.append(map(str.strip, sub.split('=', 1)))
            else:
                res.append((sub, None))
        res = dict(res)
        return res


    def copyFile(self, input_file, output_file, tokens: dict):
        p = Path(output_file.parent)
        p.mkdir(parents=True, exist_ok=True)
        input_file = open(input_file, 'r')
        output_file = open(output_file, 'w')
        for line in input_file:
            for token, value in tokens.items():
                line = re.sub("<%=[ ]*" + token + "[ ]*%>", value, line)
            output_file.write(line)

    def exec_generator(self, **kwargs):
        try:
            attrs = self.get_attrs(**kwargs)
            self.temp_name      = attrs['temp_name']
            self.temp_gzip_file = attrs['temp_gzip_file']
            self.temp_files     = attrs['temp_files']
            self.temp_tokens    = attrs['temp_tokens']
            self.output_folder  = attrs['output_folder']

            output_folder = Path(self.output_folder)
            output_folder.mkdir()

            gzipfile = Path(self.temp_gzip_file)
            if not  gzipfile.exists():
                print(f"File {str(gzipfile)} not found")
                exit(1)

            tmpdir = tempfile.TemporaryDirectory()
            gzipobj = tarfile.open(gzipfile)
            gzipobj.extractall(tmpdir.name)
            gzipobj.close()

            dir_tmptemp = Path(Path(tmpdir.name) / Path(self.temp_name))

            for tp in self.temp_files:
                fin = Path(dir_tmptemp / Path(tp))
                if fin.exists():
                    fout = Path( output_folder / Path(tp))
                    log.debug("{0} > {1}".format(str(fin), str(fout)))
                    if fin.is_dir():
                        fout.mkdir(parents=True, exist_ok=True)
                    else:
                        self.copyFile(fin, fout, self.temp_tokens)
        except FileExistsError:
            print(f"Folder {output_folder} already exist")
        except Exception as ex:
            log.exception(ex)
