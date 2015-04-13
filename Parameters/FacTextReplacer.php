<?php

require_once('FacTable.php');
require_once('FacValueExtractor.php');

class FacTextReplacer {
    private $text;
    private $value_extractor;

    function __construct($text)
    {
        $this->text = $text;
        $this->value_extractor = new FacValueExtractor($text);
    }

    function is_derived()
    {
        $is_derived = $this->value_extractor->get_value('is_derived');
        if (strtoupper($is_derived) == 'TRUE')
            return true;
        else
            return false;
    }

    function replace($values)
    {
        $text = $this->text;

        foreach ($values as $field => $value) {
            $start = FacValueExtractor::tag_begin_open . $field .
                FacValueExtractor::tag_close;
            $end = FacValueExtractor::tag_end_open . $field .
                FacValueExtractor::tag_close;
            $pos_s = strpos($text, $start);
            $pos_e = strpos($text, $end);
            $text = substr($text, 0, $pos_s+strlen($start)) . $value .
                substr($text, $pos_e);
        }

        return $text;
    }
}

?>
