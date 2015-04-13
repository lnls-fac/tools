<?php

require_once('FacFunctions.php');


class FacException extends Exception { }

class FacConnection {
    # Move to external file with appropriate permissions
    const server_address = '10.0.21.132';
    const user = 'prm_editor';
    const password = 'prm0';
    const database = 'parameters';

    protected $mysqli;

    function __construct()
    {
        $this->mysqli = new mysqli(
            self::server_address,
            self::user,
            self::password,
            self::database
        );
        if ($this->mysqli->connect_errno)
            throw new FacException('could not connect to database');
        else
            $this->mysqli->autocommit(false);
    }

    function escape($s)
    {
        return $this->mysqli->real_escape_string($s);
    }

    function query($query)
    {
        $r = $this->mysqli->query($query);
        if (!$r) {
            $this->mysqli->rollback();
            throw new FacException('database query failed');
        } else
            return $r;
    }

    function commit()
    {
        return $this->mysqli->commit();
    }
}

class FacTable extends FacConnection {
    function __construct()
    {
        parent::__construct();
    }

    function read_parameter($name)
    {
        $r = $this->read_all_with_name_from_table($name, 'parameter');

        if ($r->num_rows == 0) {
            $link = '[[Parameter:' . $name . '|' . $name . ']]';
            throw new FacException('parameter "' . $link . '" not found');
        } else {
            $row = $r->fetch_assoc();
            return $this->get_text_fields($row);
        }
    }

    function read_all_with_name_from_table($name, $table)
    {
        $query = "SELECT * FROM " . $this->escape($table) .
            " WHERE name='" . $this->escape($name) . "';";

        return $this->query($query);
    }

    function get_text_fields($cols)
    {
        $fields = array();
        foreach ($cols as $col => $value) {
            $field = $this->convert_col_to_field($col);
            if ($field == 'symbol')
                $fields[$field] = $this->append_math_tags($value);
            elseif ($field == 'is_derived')
                $fields[$field] = $this->convert_integer_to_bool_text($value);
            else
                $fields[$field] = $value;
        }
        return $fields;
    }

    function convert_col_to_field($col)
    {
        if ($col == 'team')
            return 'group';
        else
            return $col;
    }

    function append_math_tags($value)
    {
        return "<math>" . $value . "</math>";
    }

    function convert_integer_to_bool_text($value)
    {
        if ($value)
            return "True";
        else
            return "False";
    }

    function read_dependencies($name)
    {
        $r = $this->read_all_with_name_from_table($name, 'dependency');

        $rows = $r->fetch_all();

        $deps = array();
        foreach ($rows as $row)
            array_push($deps, $row[1]);

        return $deps;
    }

    function write_parameter($fields)
    {
        $db_fields = $this->get_db_fields($fields);

        $r = $this->check_parameter_exists($db_fields['name']);
        if ($r)
            $query = $this->build_update_parameter_query($db_fields);
        else
            $query = $this->build_insert_query($db_fields, 'parameter');

        $result = $this->query($query);
    }

    function get_db_fields($fields)
    {
        $db_fields = array();
        foreach ($fields as $key => $value) {
            if ($key == 'symbol')
                $db_fields[$key] = $this->strip_math_tags($value);
            elseif ($key == 'is_derived')
                $db_fields[$key] = $this->convert_bool_text_to_integer($value);
            else
                $db_fields[$key] = $this->convert_identity($value);
        }
        return $db_fields;
    }

    function check_parameter_exists($parameter)
    {
        $r = $this->read_all_with_name_from_table($parameter, 'parameter');

        if ($r->num_rows == 0)
            return false;
        else
            return true;
    }

    function build_insert_query($values, $table)
    {
        $query = "INSERT INTO " . $table . " VALUES (" .
            "'" . implode("', '", $values) . "');";
        return $query;
    }

    function build_update_parameter_query($db_fields)
    {
        $query = "UPDATE parameter SET " .
            "team='" . $db_fields['group'] . "', " .
            "symbol='" . $db_fields['symbol'] . "', " .
            "units='" . $db_fields['units'] . "', " .
            "is_derived='" . $db_fields['is_derived'] . "', " .
            "value='" . $db_fields['value'] . "' " .
            "WHERE name='" . $db_fields['name'] . "';";

        return $query;
    }

    function convert_identity($value)
    {
        return $this->escape($value);
    }

    function strip_math_tags($value)
    {
        return $this->escape(strip_tags($value));
    }

    function convert_bool_text_to_integer($value)
    {
        if (strtoupper($value) == 'TRUE')
            return 1;
        else
            return 0;
    }

    function write_dependencies($parameter, array $dependencies)
    {
        if (count($dependencies) == 0)
            return true;

        $query = "INSERT INTO dependency VALUES ";
        $values = array();

        foreach($dependencies as $dep) {
            $value = "('" . $parameter . "', '" . $dep . "')";
            array_push($values, $value);
        }
        $query .= implode(', ', $values) . ";";

        return $this->query($query);
    }

    function write_expression($parameter, $expression)
    {
        $r = $this->read_all_with_name_from_table($parameter, 'expression');
        if ($r->num_rows > 0) {
            $query = "UPDATE expression SET expression='" .
                $expression . "' WHERE name='" .
                $parameter . "';";
        } else {
            $query = "INSERT INTO expression VALUES ('" .
                $parameter . "', '" . $expression . "');";
        }

        return $this->query($query);
    }

    function rename_parameter($name, $new_name)
    {
        $tables = array('parameter', 'dependency', 'expression');
        foreach ($tables as $table) {
            $query = "UPDATE " . $table . " SET name='" .
                $new_name . "' WHERE name='" .
                $name . "';";

            $this->query($query);
        }

        return true;
    }

    function rename_dependencies($name, $new_name)
    {
        fac_write('debug', "\n* entering rename_dependencies *");
        $tables = array('dependency', 'expression');
        foreach ($tables as $table) {
            $value_col = $table;
            $query = "SELECT * FROM " . $table . " WHERE " . $value_col . " LIKE '%" . $name . "%';";
            $result = $this->query($query);
            fac_write('debug', 'after query');
            $items = $result->fetch_all();
            fac_write('debug', 'fetched');
            foreach ($items as $item) {
                fac_write('debug', 'item 1 is ' . $item[1]);
                $new_value = str_replace($name,$new_name,$item[1]);
                fac_write('debug', 'new value is ' . $new_value);
                $query = "UPDATE " . $table . " SET " . $value_col . "='" . $new_value . "' WHERE name='" . $item[0] . 
                         "' AND " . $value_col . "='" . $item[1] . "';";
                fac_write('debug', 'update query: ' . $query);
                $this->query($query);
            }
        }
    }

    function erase_parameter($parameter)
    {
        return $this->erase('parameter', $parameter);
    }

    function erase_dependencies($parameter)
    {
        return $this->erase('dependency', $parameter);
    }

    function erase_expression($parameter)
    {
        return $this->erase('expression', $parameter);
    }

    function erase($table, $parameter)
    {
        $query = "DELETE FROM " . $table . " WHERE name='" .
            $parameter . "';";

        return $this->query($query);
    }

    function read_expression($parameter)
    {
        $query = "SELECT * FROM expression WHERE name='" .
            $parameter . "';";
        $r = $this->query($query);
        if ($r->num_rows == 0) {
            $msg = 'expression for parameter "' . $parameter . '" not found';
            throw new FacException($msg);
        }

        $row = $r->fetch_assoc();
        return $row['expression'];
    }

    function get_parameter_list($subsystem, $prim_only)
    {
        if ($prim_only)
            $sel = " AND is_derived=0";
        else
            $sel = "";

        $query = "SELECT name FROM parameter WHERE name LIKE '" .
            $this->escape($subsystem) . "%'" . $sel . ";";
        $r = $this->query($query);

        return $r->fetch_all();
    }
}

class FacEvaluator extends FacConnection {
    const max_depth = 1000;

    static $valid_symbols = array(
        ' ', '.', '(', ')', ',',
        '0', '1', '2', '3', '4',
        '5', '6', '7', '8', '9',
        'e', 'E'
    );
    static $valid_operators = array('+', '-', '*', '/');
    static $valid_functions = array(
        'pi', 'deg2rad', 'rad2deg',
        'joule_2_ev', 'gamma', 'beta',
        'velocity', 'brho', 'critical_energy',
        'U0', 'sync_phase', 'rf_energy_acceptance',
        'natural_emittance', 'energy_spread', 'revolution_period',
        'revolution_frequency', 'rf_frequency', 'number_of_electrons',
        'overvoltage', 'alpha1', 'Jx',
        'Js', 'frequency_from_tune', 'damping_time',
        'radiation_power', 'rf_wavelength', 'slip_factor',
        'bunch_length', 'bunch_duration', 'id_deflection_parameter',
        'id_mean_power',
        'sqrt', 'pow', 'exp',
        'asin', 'acos', 'atan',
        'sin', 'cos', 'tan',
    );
    static $valid_constants = array(
        '$light_speed', '$vacuum_permeability', '$elementary_charge',
        '$electron_mass', '$electron_rest_energy', '$vacuum_permitticity',
        '$joule_2_eV', '$reduced_planck_constant', '$rad_cgamma',
        '$Cq', '$Ca'
    );

    private $name;
    private $expression;
    private $dependencies;
    private $parameters;
    private $depth;

    function __construct($name, $expression, $parameter=false)
    {
        parent::__construct();

        $this->name = $name;

        if ($parameter) {
            $this->parameters = array(
                $parameter['name'] => $parameter['value']
            );
        } else
            $this->parameters = array();

        $this->depth = 0;

        $r = $this->replace_parameters($expression);
        $this->expression = $r['expression'];
        $this->dependencies = $r['dependencies'];
    }

    function get_dependencies()
    {
        return $this->dependencies;
    }

    function evaluate()
    {
        global $light_speed;
        global $vacuum_permeability;
        global $elementary_charge;
        global $electron_mass;
        global $electron_rest_energy;
        global $vacuum_permitticity;
        global $joule_2_eV;
        global $reduced_planck_constant;
        global $rad_cgamma;
        global $Cq;
        global $Ca;

        if ($this->validate_final_expression($this->expression)) {
            $extended_expr = '$r = ' . $this->expression . ';';
            eval($extended_expr);
            return $r;
        } else
            throw new FacException('invalid expression for ' . $this->name);
    }

    function replace_parameters($expression)
    {
        if ($depth++ >= self::max_depth)
            throw new FacException('max depth achieved');

        if (substr_count($expression, '"') % 2)
            throw new FacException('quote mismatch');

        $dt = new FacDependencyTracker($expression);
        $deps = $dt->get_dependencies();

        foreach ($deps as $p) {
            if (!array_key_exists($p, $this->parameters))
                $this->parameters[$p] = $this->get_value_or_expression($p);

            $parameter = '"' . $p . '"';
            $value = strval($this->parameters[$p]);
            $expression = str_replace($parameter, $value, $expression);
        }

        return array('expression' => $expression, 'dependencies' => $deps);
    }

    function get_value_or_expression($parameter)
    {
        $p = $this->read_parameter($parameter);
        if ($p['is_derived']) {
            $r = $this->replace_parameters($p['value']);
            return '(' . $r['expression'] . ')';
        } else
            return $p['value'];
    }

    function read_parameter($parameter)
    {
        $query = "SELECT * FROM parameter WHERE name='" .
            $parameter . "';";
        $r = $this->query($query);

        $row = $r->fetch_assoc();
        if (!$row) {
            $msg = 'parameter "' . $parameter . '" not found';
            throw new FacException($msg);
        }

        if ($row['is_derived'])
            $value = $this->read_expression($parameter);
        else
            $value = $row['value'];

        return array('is_derived' => $row['is_derived'], 'value' => $value);
    }

    function read_expression($parameter)
    {
        $query = "SELECT * FROM expression WHERE name='" .
            $parameter . "';";
        $r = $this->query($query);

        $row = $r->fetch_assoc();
        if (!$row) {
            $msg = 'expression for "' . $parameter . '" not found';
            throw new FacException($msg);
        } else
            return $row['expression'];
    }

    function validate_final_expression($expression)
    {
        foreach (self::$valid_functions as $f)
            $expression = str_replace($f, '', $expression);
        foreach (self::$valid_constants as $c)
            $expression = str_replace($c, '', $expression);
        foreach (self::$valid_symbols as $s)
            $expression = str_replace($s, '', $expression);
        foreach (self::$valid_operators as $o)
            $expression = str_replace($o, '', $expression);

        if ($expression === '')
            return true;
        else
            return false;
    }
}

class FacDependencyTracker {
    private $expression;

    function __construct($expression)
    {
        $this->expression = $expression;
    }

    function get_dependencies()
    {
        $n = substr_count($this->expression, '"');
        if ($n % 2) {
            $msg = 'quotes in ' . $this->expression . ' did not match';
            throw new FacException($msg);
        }

        $deps = array();
        $split = explode('"', $this->expression);

        for ($i = 0; $i < count($split); $i++)
            if ($i % 2)
                array_push($deps, $split[$i]);

        return array_unique($deps);
    }
}

class FacDependentTracker extends FacConnection {
    private $parameter;

    function __construct($parameter)
    {
        parent::__construct();
        $this->parameter = $parameter;
    }

    function get_dependents()
    {
        $query = "SELECT * FROM dependency;";
        $r = $this->query($query);

        $table = array();
        for ($i = 0; $i < $r->num_rows; $i++) {
            array_push($table, $r->fetch_row());
        }

        $s = new FacSet();
        $t = new FacSet();
        $t->put($this->parameter);
        $n = $s->count();

        while (true) {
            $u = new FacSet();
            foreach ($table as $row)
                foreach($t->elements as $e)
                    if ($row[1] == $e) {
                        $u->put($row[0]);
                        $s->put($row[0]);
                    }

            $new_n = $s->count();
            if ($new_n > $n) {
                $n = $new_n;
                $t = $u;
            } else
                break;
        }

        return $s->elements;
    }
}

class FacSet {
    public $elements = array();

    function put($x)
    {
        if (!in_array($x, $this->elements))
            array_push($this->elements, $x);
    }

    function count()
    {
        return count($this->elements);
    }
}

function fac_write($filename, $text)
{
    $f = fopen('/tmp/' . $filename . '.txt', 'a');
    fwrite($f, $text . "\n");
    fclose($f);
}

?>
