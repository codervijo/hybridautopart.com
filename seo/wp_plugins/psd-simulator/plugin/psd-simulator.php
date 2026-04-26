<?php
/**
 * Plugin Name: PSD Simulator
 * Plugin URI:  https://hybridautopart.com/blog-en/toyota-prius-power-split-device/
 * Description: Interactive Toyota Power Split Device simulator with real Willis equation physics. Use shortcode [psd_simulator].
 * Version:     0.1.0
 * Author:      hybridautopart.com
 * License:     GPL-2.0-or-later
 * Text Domain: psd-simulator
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

define( 'PSD_SIM_VERSION', '0.1.0' );
define( 'PSD_SIM_DIR',     plugin_dir_path( __FILE__ ) );
define( 'PSD_SIM_URL',     plugin_dir_url( __FILE__ ) );

/**
 * Shortcode: [psd_simulator height="750px" theme="dark"]
 */
function psd_simulator_shortcode( $atts ) {
    $atts = shortcode_atts(
        array(
            'height' => '750px',
            'theme'  => 'dark',
        ),
        $atts,
        'psd_simulator'
    );

    $dist    = PSD_SIM_URL . 'dist/';
    $version = PSD_SIM_VERSION;
    $height  = esc_attr( $atts['height'] );
    $theme   = esc_attr( $atts['theme'] );

    // Stylesheet
    wp_enqueue_style(
        'psd-simulator',
        $dist . 'psd-simulator.css',
        array(),
        $version
    );

    // React bundle (module — type="module" set via script_loader_tag filter below)
    wp_enqueue_script(
        'psd-simulator',
        $dist . 'psd-simulator.js',
        array(),
        $version,
        true   // load in footer
    );

    return sprintf(
        '<div id="psd-root" data-theme="%s" style="min-height:%s;background:#0f172a;border-radius:12px;overflow:hidden;"></div>',
        $theme,
        $height
    );
}
add_shortcode( 'psd_simulator', 'psd_simulator_shortcode' );

/**
 * Add type="module" to the psd-simulator script tag so Vite's ES module
 * bundle loads correctly in the browser.
 */
function psd_simulator_script_type( $tag, $handle, $src ) {
    if ( 'psd-simulator' !== $handle ) {
        return $tag;
    }
    return str_replace( '<script ', '<script type="module" ', $tag );
}
add_filter( 'script_loader_tag', 'psd_simulator_script_type', 10, 3 );
