<?php
/*
 * Parameters extension
 *
 * Include parameterised and derived values in articles.
 */

if (!defined('MEDIAWIKI')) {
    echo("This is an extension to the MediaWiki package and cannot be run ".
        "standalone.\n");
    die(-1);
}

require_once('FacParameter.php');
require_once('FacTextReplacer.php');

$wgExtensionCredits['other'][] = array(
    'name' => 'Parameters',
    'version' => '0.5.0',
    'author' => array('Afonso Haruo Carnielli Mukai'),
    'description' => 'Include parameterised and derived values in articles'
);

$wgHooks['ParserFirstCallInit'][] = 'fac_parameter_parser_init';
$wgHooks['EditFormPreloadText'][] = 'fac_edit_form_preload_text';
$wgHooks['EditFormInitialText'][] = 'fac_edit_form_initial_text';
$wgHooks['EditPageGetPreviewContent'][] = 'fac_edit_page_get_preview_content';
$wgHooks['EditFilter'][] = 'fac_edit_filter';
$wgHooks['PageContentSave'][] = 'fac_page_content_save';
$wgHooks['TitleMove'][] = 'fac_title_move';
$wgHooks['AbortMove'][] = 'fac_abort_move';
$wgHooks['ArticleDelete'][] = 'fac_article_delete';

function fac_parameter_parser_init(Parser $parser)
{
    $parser->setHook("sirius", "fac_sirius_parameter_render");
    $parser->setHook("sirius_value", "fac_sirius_value_parameter_render");
    $parser->setHook("sirius_units", "fac_sirius_units_parameter_render");
    $parser->setHook("dependencies", "fac_dependencies_parameter_render");
    $parser->setHook("dependents", "fac_dependents_parameter_render");
    $parser->setHook("parameter_list", "fac_parameter_list_parameter_render");
    $parser->setHook("math_expr", "fac_math_expression_render");

    return true;
}

function fac_sirius_parameter_render($input, array $args, Parser $parser,
    PPFrame $frame)
{
    try {
        $prm = new FacParameterReader($input);
        $fields = $prm->read();
        $output = fac_get_sirius_parameter_with_args($fields, $args);
    } catch(FacException $e) {
        $output = fac_get_error_message('Error: ' . $e->getMessage());
    }

    return $parser->recursiveTagParse($output, $frame);
}

function fac_get_sirius_parameter_with_args($fields, $args)
{
    $field = fac_get_arg_value('field', $args);
    $format = fac_get_arg_value('format', $args);
    $link = fac_get_arg_value('link', $args);
    $a = fac_get_arg_value('a', $args);
    $b = fac_get_arg_value('b', $args);

    if ($a or $b)
        $fields['value'] = fac_apply_affine($fields['value'], $a, $b);

    if ($format)
        $fields['value'] = fac_format_value($format, $fields['value']);

    if (strtoupper($link) != 'FALSE') {
        $v = fac_get_parameter_link($fields['name'], $fields['value']);
        $fields['value'] = $v;
    }

    if ($field)
        return $fields[$field];
    else
        return $fields['value'] . " " . $fields['units'];
}

function fac_get_arg_value($arg, array $args)
{
    if (array_key_exists($arg, $args))
        return $args[$arg];
    else
        return false;
}

function fac_apply_affine($value, $a, $b)
{
    if ($a === false)
        $a = 1;
    else
        $a = floatval($a);

    if ($b === false)
        $b = 0;
    else
        $b = floatval($b);

    return strval($a*floatval($value) + $b);
}

function fac_format_value($format, $value)
{
    $s = strtolower(sprintf($format, $value));
    $p = strpos($s, 'e');
    if ($p !== false) {
        if ($s{$p+1} == '-') { $e = substr($s, $p, 1); } else  { $e = substr($s, $p, 2); }
 	    $s = str_replace($e, '×10<sup>', $s) . '</sup>';
    }

    return $s;
}

function fac_get_error_message($msg)
{
    $s = fac_get_coloured_text($msg);
    $s = fac_get_bold_text($s);

    return $s;
}

function fac_get_bold_text($text)
{
    return "'''" . $text . "'''";
}

function fac_get_coloured_text($text, $colour='red')
{
    return '<span style="color: ' . $colour . '">' . $text . '</span>';
}

function fac_sirius_value_parameter_render($input, array $args,
    Parser $parser, PPFrame $frame)
{
    $args['field'] = 'value';
    return fac_sirius_parameter_render($input, $args, $parser, $frame);
}

function fac_sirius_units_parameter_render($input, array $args,
    Parser $parser, PPFrame $frame)
{
    $args['field'] = 'units';
    $args['link'] = 'FALSE';
    return fac_sirius_parameter_render($input, $args, $parser, $frame);
}

function fac_dependencies_parameter_render($input, array $args,
    Parser $parser, PPFrame $frame)
{
    try {
        $prm = new FacParameterReader($input);
        $deps = $prm->read_dependencies();
        $deps_with_links = fac_add_link_to_parameters($deps);
        $output = implode(', ', $deps_with_links);
    } catch(FacException $e) {
        $output = fac_get_error_message('Error: ' . $e->getMessage());
    }

    return $parser->recursiveTagParse($output, $frame);
}

function fac_add_link_to_parameters($parameters)
{
    $result = array();
    foreach ($parameters as $p) {
        $s = fac_get_parameter_link($p);
        array_push($result, $s);
    }
    return $result;
}

function fac_get_parameter_link($name, $label=false)
{
    if (!$label)
        $label = $name;

    $s = '[[' . FacParameter::parameter_namespace . $name . '|'
        . $label . ']]';
    return $s;
}

function fac_dependents_parameter_render($input, array $args, Parser $parser,
    PPFrame $frame)
{
    try {
        $prm = new FacParameterReader($input);
        $deps = $prm->read_dependents();
        $deps_with_links = fac_add_link_to_parameters($deps);
        $output = implode(', ', $deps_with_links);
    } catch(FacException $e) {
        $output = fac_get_error_message('Error: ' . $e->getMessage());
    }

    return $parser->recursiveTagParse($output, $frame);
}

function fac_parameter_list_parameter_render($input, array $args,
    Parser $parser, PPFrame $frame)
{
    $prim_only = fac_get_arg_value('selection', $args);
    if ($prim_only && (strtolower($prim_only) == 'primitive'))
        $prim_only = true;
    else
        $prim_only = false;

    try {
        $prm = new FacParameterLister($input);
        $list = $prm->get_list($prim_only);
        if ($list === false) {
            $error = 'Error: subsystem ' . $input . ' not found';
            $output = fac_get_error_message($error);
        } else {
            $list = fac_add_link_to_parameters($list);
            $output = fac_get_parameter_list_text($list);
        }
    } catch(FacException $e) {
        $output = fac_get_error_message('Error: ' . $e->getMessage());
    }

    return $parser->recursiveTagParse($output, $frame);
}

function fac_get_parameter_list_text($parameters)
{
    $last = array_pop($parameters);

    $text = "";
    foreach($parameters as $p)
        $text .= "# " . $p . "\n";

    $text .= "# " . $last;

    return $text;
}

function fac_math_expression_render($input, array $args, Parser $parser,
    PPFrame $frame)
{
    try {
        $evaluator = new FacMathExpressionEvaluator($input);
        $output = $evaluator->evaluate();
    } catch (FacException $e) {
        $output = fac_get_error_message('Error: ' . $e->getMessage());
    }

    $format = fac_get_arg_value('format', $args);
    if ($format !== false)
        $output = fac_format_value($format, $output);

    return $parser->recursiveTagParse($output, $frame);
}

function fac_edit_form_preload_text(&$text, &$title)
{
    $name = FacParameter::get_name_if_parameter($title);
    if (!$name)
        return true; # not a parameter page

    $text = FacParameter::get_parameter_template($name);
    return true;
}

function fac_edit_form_initial_text($editPage)
{
    $name = FacParameter::get_name_if_parameter($editPage->getTitle());
    if (!$name)
        return true; # not a parameter page

    try {
        $prm = new FacParameterReader($name);
        $fields = $prm->read();

        if (strtoupper($fields['is_derived']) != 'TRUE')
            return true;

        $expression = $prm->read_expression();
    } catch(FacException $e) {
        return false;
    }

    $text = $editPage->textbox1;
    $replacer = new FacTextReplacer($text);
    $new_text = $replacer->replace(array('value' => $expression));

    $editPage->textbox1 = $new_text;

    return true;
}

function fac_edit_page_get_preview_content($editPage, &$content)
{
    $name = FacParameter::get_name_if_parameter($editPage->getTitle());
    if (!$name)
        return true; # not a parameter page

    $text = $content->getNativeData();
    $prm = new FacParameterWriter($name, $text);

    try {
        $r = $prm->check();
        if (!$r) {
            $err = fac_get_missing_fields_message($prm->missing_fields);
            $text .= "\n" . $err;
            $content = new Wikitextcontent($text);
            return true;
        } elseif (!is_array($r))
            return true; # not a derived parameter
    } catch(FacException $e) {
        $msg = fac_get_bold_text('Error: ' . $e->getMessage());
        $text .= "\n" . fac_get_coloured_text($msg);
        $content = new Wikitextcontent($text);
        return true;
    }

    $replacer = new FacTextReplacer($text);
    $new_values = fac_get_derived_values_to_replace($r);
    $new_text = $replacer->replace($new_values);
    $content = new WikitextContent($new_text);

    return true;
}

function fac_get_derived_values_to_replace($fields)
{
    $deps = array();
    foreach ($fields['dependencies'] as $d)
        array_push($deps, fac_get_parameter_link($d));

    $new_values = array(
        'value' => $fields['value'],
        'deps' => implode(', ', $deps)
    );

    return $new_values;
}

function fac_edit_filter($editor, $text, $section, &$error, $summary)
{
    $name = FacParameter::get_name_if_parameter($editor->getTitle());
    if (!$name)
        return true; # not a parameter page

    try {
        $prm = new FacParameterWriter($name, $text);
        $result = $prm->write();
        if (!$result)
            $error = fac_get_missing_fields_message($prm->missing_fields);
    } catch (FacException $e) {
        $error = fac_get_error_message('Error: ' . $e->getMessage());
    }

    return true;
}

function fac_get_missing_fields_message($missing_fields)
{
    $msg = "Missing field";
    if (count($missing_fields) > 1)
        $msg .= "s";
    $field_list = htmlspecialchars(implode(', ', $missing_fields));
    $msg .= ": " . $field_list;

    return fac_get_error_message($msg);
}

function fac_page_content_save(&$wikiPage, &$user, &$content, &$summary,
    $isMinor, $isWatch, $section, &$flags, &$status)
{
    $name = FacParameter::get_name_if_parameter($wikiPage->getTitle());
    if (!$name)
        return true; # not a parameter page

    $text = $content->getNativeData();
    $replacer = new FacTextReplacer($text);

    if (!$replacer->is_derived())
        return true;

    # Fields and values to replace
    $values = array(
        'value' => '<sirius_value link=False>' . $name . '</sirius_value>',
        'deps' => '<dependencies>' . $name . '</dependencies>'
    );

    $new_text = $replacer->replace($values);
    $content = new WikitextContent($new_text);

    return true;
}

function fac_title_move(Title $title, Title $newTitle, User $user)
{
    $ns = substr(FacParameter::parameter_namespace, 0, -1); # remove colon

    $old_ns = $title->getSubjectNsText();
    $new_ns = $newTitle->getSubjectNsText();

    if(($old_ns != $ns) or ($new_ns != $ns))
        return true; # not in parameter namespace

    try {
        $prm = new FacParameterWriter($title->getText());
        $prm->rename($newTitle->getText());
    } catch(FacException $e) {
        return false;
    }

    return true;
}

function fac_abort_move(Title $oldTitle, Title $newTitle, User $user,
    &$error, $reason)
{
    $ns = substr(FacParameter::parameter_namespace, 0, -1); # remove colon

    if ($oldTitle->getSubjectNsText() != $ns) {
        if ($newTitle->getSubjectNsText() == $ns) {
            $error = 'Cannot move to parameter namespace';
            return false;
        }
    } else {
        if ($newTitle->getSubjectNsText() != $ns) {
            $error = 'Cannot move out of parameter namespace';
            return false;
        } else {
            if ($newTitle->exists()) {
                $error = 'Cannot overwrite existing parameter';
                return false;
            }
        }
    }

    return true;
}

function fac_article_delete(WikiPage &$wikiPage, User &$user, &$reason,
    &$error)
{
    $name = FacParameter::get_name_if_parameter($wikiPage->getTitle());
    if (!$name)
        return true; # not a parameter page

    try {
        $prm_reader = new FacParameterReader($name);
        $deps = $prm_reader->read_dependents();
        if (count($deps) > 0) {
            $list = implode(', ', $deps);
            $msg = 'Cannot erase parameter with dependents (' . $list . ')';
            $error = fac_get_coloured_text($msg);
            return false;
        }

        $prm_eraser = new FacParameterEraser($name);
        $prm_eraser->erase();
        return true;
    } catch(FacException $e) {
        $error = fac_get_coloured_text($e->getMessage());
        return false;
    }
}

?>
