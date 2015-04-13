<?php

class FacValueExtractor {
    const tag_begin_open = "<section begin=";
    const tag_end_open = "<section end=";
    const tag_close = "/>";

    var $text;

    function __construct($text)
    {
        $this->text = $text;        
    }

    function get_value($field)
    {
        $start = self::tag_begin_open . $field . self::tag_close;
        $end = self::tag_end_open . $field . self::tag_close;
        return $this->extract_text_between($start, $end);
    }

    private function extract_text_between($start, $end)
    {
        $len_s = strlen($start);
        $pos_s = strpos($this->text, $start);
        $pos_e = strpos($this->text, $end);

        if ($pos_s===false || $pos_e===false)
            return false;

        $result = substr($this->text, $pos_s+$len_s, $pos_e-$pos_s-$len_s);
        
        return $result;
    }
}

?>
