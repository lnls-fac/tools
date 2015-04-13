<?php

require_once('FacTable.php');
require_once('FacValueExtractor.php');


class FacParameter {
    const parameter_namespace = "Parameter:";

    static $valid_fields = array(
        'group', 'symbol', 'units', 'is_derived', 'value'
    );

    protected $parameter;

    public static function get_name_if_parameter($title)
    {
        $n = strlen(self::parameter_namespace);
        if (substr($title, 0, $n) != self::parameter_namespace)
            return false;
        else
            return substr($title, $n);
    }

    public static function get_parameter_template($name)
    {
        $template = "==Data==\n" .
            "<section begin=data/>\n" .
            "* Group: <section begin=group/><section end=group/>\n" .
            "* Symbol: <section begin=symbol/><section end=symbol/>\n" .
            "* Derived: <section begin=is_derived/>False<section end=is_derived/>\n" .
            "* Value: <section begin=value/><section end=value/>\n" .
            "* Units: <section begin=units/><section end=units/>\n" .
            "* Dependencies: <section begin=deps/><dependencies>" . $name . "</dependencies><section end=deps/>\n" .
            "<section end=data/>\n" .
            "==Observations==\n" .
            "<section begin=obs/>\n" .
            "<section end=obs/>";
        return $template;
    }

    function __construct($name)
    {
        $this->parameter = $name;
    }
}

class FacParameterReader extends FacParameter {
    function __construct($name)
    {
        parent::__construct($name);
    }

    function read()
    {
        $table = new FacTable();
        return $table->read_parameter($this->parameter);
    }

    function read_expression()
    {
        $table = new FacTable();
        return $table->read_expression($this->parameter);
    }

    function read_dependencies()
    {
        $table = new FacTable();
        $deps = $table->read_dependencies($this->parameter);
        sort($deps);
        return $deps;
    }

    function read_dependents()
    {
        $dt = new FacDependentTracker($this->parameter);
        $deps = $dt->get_dependents();
        sort($deps);
        return $deps;
    }
}

class FacParameterWriter extends FacParameter {
    public $missing_fields = array();
    private $value_extractor;

    function __construct($name, $text)
    {
        parent::__construct($name);
        $this->value_extractor = new FacValueExtractor($text);
    }

    function write()
    {
        $values = $this->get_values();
        if ($this->has_missing_fields($values))
            return false;
        else
            return $this->write_all($values);
    }

    private function get_values()
    {
        $values = array('name' => $this->parameter);
        foreach (self::$valid_fields as $field)
            $values[$field] = $this->get_value($field);

        return $values;
    }

    private function get_value($field)
    {
        if (in_array($field, self::$valid_fields)) {
            return $this->value_extractor->get_value($field);
        } else
            return false;
    }

    private function has_missing_fields($values)
    {
        foreach ($values as $field => $value)
            if ($value === false) # empty string is valid, so check for ===
                array_push($this->missing_fields, $field);

        return (count($this->missing_fields) > 0);
    }

    private function write_all($values)
    {
        $table = new FacTable();
        $table->erase_dependencies($values['name']);
        $table->erase_expression($values['name']);

        if ($values['is_derived'] === 'True')  {
            $e = new FacEvaluator($values['name'], $values['value'], $values);
            $this->write_derived_fields(
                $values,
                $e->get_dependencies(),
                $table
            );
            $values['value'] = $e->evaluate();
        }

        $table->write_parameter($values);
        $this->update_dependents($values, $table);

        return $table->commit();
    }

    private function write_derived_fields($parameter, $dependencies, $table)
    {
        $table->write_dependencies($this->parameter, $dependencies);
        $table->write_expression($this->parameter, $parameter['value']);
    }

    private function update_dependents($parameter, $table)
    {
        $dt = new FacDependentTracker($parameter['name']);
        $dependents = $dt->get_dependents();
        foreach($dependents as $d) {
            $p = $table->read_parameter($d);
            $e = new FacEvaluator(
                $p['name'],
                $table->read_expression($p['name']),
                $parameter
            );
            $p['value'] = $e->evaluate();
            $table->write_parameter($p);
        }
    }

    function rename($new_name)
    {
        $table = new FacTable();
        $table->rename_parameter($this->parameter, $new_name);
        $table->rename_dependencies($this->parameter, $new_name);

        return $table->commit();
    }

    function check()
    {
        $values = $this->get_values();
        if ($this->has_missing_fields($values))
            return false;

        if (strtolower($values['is_derived']) != 'true')
            return true;

        $e = new FacEvaluator($values['name'], $values['value'], $values);
        $value = $e->evaluate();
        $deps = $e->get_dependencies();

        return array('value' => $value, 'dependencies' => $deps);
    }
}

class FacParameterEraser extends FacParameter {
    function __construct($name)
    {
        parent::__construct($name);
    }

    function erase()
    {
        $table = new FacTable();

        $table->erase_dependencies($this->parameter);
        $table->erase_expression($this->parameter);
        $table->erase_parameter($this->parameter);

        return $table->commit();
    }
}

class FacParameterLister {
    static $valid_subsystems = array('LI', 'TB', 'BO', 'TS', 'SI');
    private $subsystem;

    function __construct($subsystem)
    {
        $this->subsystem = $subsystem;
    }

    function get_list($prim_only=false)
    {
        if (!in_array($this->subsystem, self::$valid_subsystems))
            return false;

        $table = new FacTable();
        $parameters = $table->get_parameter_list($this->subsystem, $prim_only);

        $list = array();
        foreach ($parameters as $p)
            array_push($list, $p[0]);

        sort($list);

        return $list;
    }
}

?>
