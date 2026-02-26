import inspect

from pydantic import TypeAdapter, ValidationError

from experiment.experiment_data import ExperimentDegrees, ExperimentRecords
from experiment.tree_experiment_runner import TreeExperimentRunner
from typing import List, IO
from core.bplus_tree import BplusTree
from core.structures.record import Record


class Tui:
    #TODO: Context Manager to easier inner menus handling ()
    #TODO: Predefined Presentation files
    _bad_command_format_mess: str = "bad command format: pick command from suggestion bellow"

    def __init__(self, t: BplusTree, exp_runner: TreeExperimentRunner):
        self.tree = t
        self.experiment_runner = exp_runner
        self.collapse_records = True


    def run(self):
        enter_mess = (
            "Type value as command\n"
            "1 Read Op Keyboard, 2 Read Ops File , 3 Run Experiment, "
            "4 Print State, 5 Settings, 9 Exit\n"
        )
        self.clear_console()
        while (cmd := input(enter_mess)) != "9":
            self.clear_console()
            match cmd:
                case "1": self.menu_keyboard_ops()
                case "2": self.read_ops_from_file()
                case "3": self.run_experiment_menu()
                case "4":self.menu_print_tree()
                case "5": self.menu_set_conf()

                case _:print(self._bad_command_format_mess);
        self.clear_console()

    def clear_console(self):
        print("\n" * 40)

    def _validate_mass(self, mS: str) -> float:
        m =  float(mS)
        if m < 0.0:
            raise ValueError("Value Error: Mass should be positive number")
        return m

    def _validate_velocity(self, vS: str) -> float:
        v = float(vS)
        if v < 0.0:
            raise ValueError("Mass is positive number")
        return v

    def _validate_key(self, kS: str) -> int:
        k = int(kS)
        if k < 0.0:
           raise ValueError("Mass is positive number")
        return k


    def _validate_record(self, line: List) -> Record:
        if len(line) != Record.ARG_COUNT:
            raise ValueError("There should be only 2 arguments, Try again")
        m = self._validate_mass(line[0])
        v = self._validate_velocity(line[1])

        return Record(mass=m, velocity=v)


    def _read_keyboard_insert(self):
        mess = "Type data to be inserted (key mass velocity) e.g: 8 3.1 1.2\n"
        inp = input(mess)
        lines = inp.strip().split()

        if len(lines) != Record.ARG_COUNT + 1:
            raise ValueError(f"To much arguments, insert have {Record.ARG_COUNT + 1}")
        key = self._validate_key(lines[0])
        rec = self._validate_record(lines[1:])

        self.tree.insert(key, rec)
        print(f"Inserted {rec} with key {key}")


    def _read_keyboard_search(self):
        mess = "Type searched key as whole number\n"
        inp = input(mess)
        lines = inp.strip().split()

        key = self._validate_key(lines[0])

        rec = self.tree.search(key)
        print(f"Record with key {key} found {rec}")


    def _read_keyboard_update(self):
        mess = ("Type data to be updated (key new_key mass velocity) e.g: 8 12 3.1 1.2,"
                "(if you want to update just record pass the same key)\n")
        inp = input(mess)
        lines = inp.strip().split()

        if len(lines) != Record.ARG_COUNT + 2:
            raise ValueError(f"To much arguments, insert have {Record.ARG_COUNT + 1}")
        key = self._validate_key(lines[0])
        new_key = self._validate_key(lines[1])
        rec = self._validate_record(lines[2:])

        self.tree.update(key, new_key, rec)
        print(f"Updated {rec} with key {new_key}")


    def _read_keyboard_delete(self):
        mess = "Type key to be deleted as whole number\n"
        key: int

        inp = input(mess)
        lines = inp.strip().split()

        key = self._validate_key(lines[0])

        rec = self.tree.delete(key)
        print(f"Deleted {rec} with {key} Deleted")



    def menu_keyboard_ops(self):
        enter_mess = (
            "Type number as command from list below\n"
            "1 Read , 2 Insert, 3 Delete, 4 update, 9 return\n"
        )
        if self.collapse_records: self.tree.display("structure_collapse_rec")
        else: self.tree.display("structure")
        while (op :=  input(enter_mess)) != "9":
            self.clear_console()
            try:
                match op:
                    case "1": self._read_keyboard_search()
                    case "2": self._read_keyboard_insert()
                    case "3": self._read_keyboard_delete()
                    case "4": self._read_keyboard_update()
                    case _: print(self._bad_command_format_mess)
            except ValueError or IndexError or TypeError or RuntimeError as e:
                self.clear_console()
                print(f"Bad Operation, {e}")
            finally:
                if self.collapse_records: self.tree.display("structure_collapse_rec")
                else: self.tree.display("structure")
        self.clear_console()


    def read_ops_from_file(self):
        mess = (
            f"Type filepath to your own file placed inside of data/ops or type return\n"
            f"Or you can use templates path (min_h2.txt"
            f" or max_h2.txt or max_h3.txt or min_h3.txt )\n"
        )
        while True:
            filepath = "data/ops/"
            filepath += input(mess)
            if filepath == "return": break

            try:
                with open(filepath, 'r') as f: self.process_ops_file(f)
                break
            except OSError as e:
                print(f"Error opening file:  {e}")
        self.clear_console()


    def _process_op(self, op: str, args: List):
        match op:
            case "read":
                key = self._validate_key(args[0])
                self.tree.search(key)

            case "delete":
                key = self._validate_key(args[0])
                self.tree.delete(key)

            case "insert":
                key = self._validate_key(args[0])
                rec = self._validate_record(args[1:])
                self.tree.insert(key, rec)

            case "update":
                key = self._validate_key(args[0])
                new_key = self._validate_key(args[1])
                rec = self._validate_record(args[2:])
                self.tree.update(key, new_key, rec)

        # if self.collapse_records: self.tree.display("structure_collapse_rec")
        # else:self.tree.display("structure")


    def process_ops_file(self, f: IO) -> None:
        lines = f.readlines()
        i: int = 0
        try:
            for i, line in enumerate(lines):
                line = line.strip().split()
                op: str = line[0]
                self._process_op(op, line[1:])

        except ValueError or IndexError or TypeError or RuntimeError as e:
            print(f"Bad Operation, line {i}, {e}")


    def menu_print_tree(self):
        enter_mess = (
            "Type value as command\n"
            "1 Structure, 2 Leafs, 3 Sequential, 4 Structure Records Collapsed,  9 return\n"
        )
        while (op := input(enter_mess)) != "9":
            self.clear_console()
            match op:
                case "1": self.tree.display("structure");
                case "2": self.tree.display("leafs");
                case "3": self.tree.display("sequential");
                case "4": self.tree.display("structure_collapse_rec");
                case _: print(self._bad_command_format_mess)
        self.clear_console()


    def _read_experiment_degrees_data(self) -> ExperimentDegrees | None:
        enter_mes = (
            "Type paremeters in format (name operation_amount reocrds_amount, d1 r1, d2 r2, d3 r4, ....) or type return\n"
            "Example input: exp1 100 1000, 2 2, 4 4\n"
        )
        adapter = TypeAdapter(ExperimentDegrees)

        while True:
            try:
                raw = input(enter_mes)
                if raw == "return": break

                raw = raw.strip().split(",")
                params = raw[0].strip().split(" ")
                data = [tuple(r_d.strip().split()) for r_d in raw[1:]]

                fields = inspect.signature(ExperimentDegrees).parameters.keys()
                values = [*params, data]
                input_dict = dict(zip(fields, values))

                return adapter.validate_python(input_dict)
            except ValidationError as e:
                self.clear_console()
                print(f"Error: {e.errors()}\n in data validation check your data format")
            except (TypeError, AttributeError, IndexError, ValueError) as e:
                self.clear_console()
                print(f"bad data format: {e} recheck your format")
        self.clear_console()
        return None

    def _read_experiment_records_data(self) -> ExperimentRecords | None:

        enter_mes = (
            "Type parameters in format (name operation_amount d r, N, N, N, ....) N is records amount or type return\n"
            "Example input: exp1 1000 4 4, 2000, 4000, 8000\n"
        )
        adapter = TypeAdapter(ExperimentRecords)
        while True:
            try:
                raw = input(enter_mes)
                if raw == "return": break

                raw = raw.strip().split(",")
                params = raw[0].strip().split(" ")
                data = raw[1:]

                fields = inspect.signature(ExperimentRecords).parameters.keys()
                values = [*params, data]
                input_dict = dict(zip(fields, values))

                return adapter.validate_python(input_dict)
            except ValidationError as e:
                self.clear_console()
                print(f"Error: {e.errors()}\n in data validation check your data format")
            except (TypeError, AttributeError, IndexError, ValueError) as e:
                self.clear_console()
                print(f"bad data format: {e}, recheck your format")
        self.clear_console()
        return None

    def _experiment_settings_menu(self):
        enter_mess = (
            "Type value as command\n"
            "1 Switch Print Phases, 2 Switch Use Real Tree Height, \n"
            "3 Switch Plot Results, 4 Switch Save Results  9 return\n"
        )
        self.clear_console()
        while (cmd:=input(enter_mess)) != "9":
            self.clear_console()
            match cmd:
                case "1":
                    self.experiment_runner.print_info = not self.experiment_runner.print_info
                    print(f"Print info changed to {self.experiment_runner.print_info}")
                case "2":
                    self.experiment_runner.use_real_height = not self.experiment_runner.use_real_height
                    print(f"Use Real tree height changed to {self.experiment_runner.use_real_height}")
                case "3":
                    self.experiment_runner.show_chart_and_table = not self.experiment_runner.show_chart_and_table
                    print(f"Plot Results changed to {self.experiment_runner.show_chart_and_table}")
                case "4":
                    self.experiment_runner.save_chart_and_table = not self.experiment_runner.save_chart_and_table
                    print(f"Save Results changed to {self.experiment_runner.save_chart_and_table}")
                case _:
                    print(f"{self._bad_command_format_mess}")
        self.clear_console()

    def run_experiment_menu(self):
        enter_mess = (
            "Type value as command\n"
            "1 Default Degrees, 2 Default Records, 3 Degrees Reverse\n"
            "4 Custom Degrees, 5 Custom Records, 6 Settings, 9 return\n"
        )
        self.clear_console()
        while (op := input(enter_mess)) != "9":
            self.clear_console()
            match op:
                case "1":
                    self.experiment_runner.run_experiment_degrees(ExperimentDegrees.DEFAULT)
                case "2":
                    self.experiment_runner.run_experiment_records(ExperimentRecords.DEFAULT)
                case "3":
                    self.experiment_runner.run_experiment_degrees(ExperimentDegrees.REVERSE_DEFAULT)
                case "4":
                    exp = self._read_experiment_degrees_data()
                    if exp is not None:
                        self.experiment_runner.run_experiment_degrees(exp)
                case "5":
                    exp = self._read_experiment_records_data()
                    if exp is not None:
                        self.experiment_runner.run_experiment_records(exp)
                case "6":
                    self._experiment_settings_menu()
                case _:
                    print(self._bad_command_format_mess)
        self.clear_console()


        print("Experiment completed")

    def menu_set_conf(self):
        enter_mess = (
            "Type value as command\n"
            "1 template Presentation (Overrides File), 2 template Default (Overrides File),\n"
            "3 Debug, 4 Switch Collapse Records, "
            "5 Clear File, 9 return\n"
        )
        while (op := input(enter_mess)) != "9":
            self.clear_console()
            match op:
                case "1":
                    self.tree.set_conf_by_template("presentation")
                    print("Configuration set to Presentation")
                case "2":
                    self.tree.set_conf_by_template("default")
                    print("Configuration set to Default")
                case "3":
                    switched = not self.tree.get_conf_attribute("debug")
                    self.tree.set_conf_attribute(debug=switched)
                    print(f"Debug set to {switched}")
                case "4":
                    self.collapse_records = not self.collapse_records
                    print(f"Collapse records set to {self.collapse_records}")
                case "5":
                    self.tree.reload_file(override=True)
                case _: print(self._bad_command_format_mess)
        self.clear_console()
