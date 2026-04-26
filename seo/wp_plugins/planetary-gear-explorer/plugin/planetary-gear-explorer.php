<?php
/**
 * Plugin Name:       Planetary Gear Ratio Explorer
 * Plugin URI:        https://wordpress.org/plugins/planetary-gear-explorer/
 * Description:       Interactive planetary (epicyclic) gear ratio calculator and animator. Enter tooth counts, choose which shaft is fixed/input/output, and watch the gears animate in real time. Includes the Willis equation with live substituted values. Use shortcode [planetary_gear_explorer].
 * Version:           0.1.0
 * Requires at least: 6.0
 * Requires PHP:      7.4
 * Author:            hybridautopart
 * Author URI:        https://hybridautopart.com
 * License:           GPL-2.0-or-later
 * License URI:       https://www.gnu.org/licenses/gpl-2.0.html
 * Text Domain:       planetary-gear-explorer
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

define( 'PGX_VERSION', '0.1.0' );
define( 'PGX_DIR',     plugin_dir_path( __FILE__ ) );
define( 'PGX_URL',     plugin_dir_url( __FILE__ )  );

/**
 * Render the shortcode.
 *
 * Usage: [planetary_gear_explorer zsun="30" zring="78" fixed="carrier" input="sun" rpm="1000" height="700px"]
 *
 * All attributes are optional — React sets sensible defaults.
 *
 * @param array $atts Shortcode attributes.
 * @return string HTML output.
 */
function pgx_shortcode( $atts ) {
    $atts = shortcode_atts(
        array(
            'zsun'   => '30',
            'zring'  => '78',
            'fixed'  => 'carrier',
            'input'  => 'sun',
            'rpm'    => '1000',
            'height' => '700px',
        ),
        $atts,
        'planetary_gear_explorer'
    );

    // Sanitize integers
    $zsun  = absint( $atts['zsun']  );
    $zring = absint( $atts['zring'] );
    $rpm   = absint( $atts['rpm']   );

    // Sanitize enum values
    $allowed_shafts = array( 'sun', 'ring', 'carrier' );
    $fixed  = in_array( $atts['fixed'], $allowed_shafts, true ) ? $atts['fixed'] : 'carrier';
    $input  = in_array( $atts['input'], $allowed_shafts, true ) ? $atts['input'] : 'sun';
    $height = esc_attr( $atts['height'] );

    $dist = PGX_URL . 'dist/';

    wp_enqueue_style(
        'planetary-gear-explorer',
        $dist . 'pgx.css',
        array(),
        PGX_VERSION
    );

    wp_enqueue_script(
        'planetary-gear-explorer',
        $dist . 'pgx.js',
        array(),
        PGX_VERSION,
        true
    );

    // Pass shortcode attributes to the React app via data attributes.
    // React reads these on mount and sets initial state.
    return sprintf(
        '<div id="pgx-root" data-zsun="%d" data-zring="%d" data-fixed="%s" data-input="%s" data-rpm="%d" style="min-height:%s;background:#0f172a;border-radius:12px;overflow:hidden;"></div>',
        $zsun,
        $zring,
        esc_attr( $fixed ),
        esc_attr( $input ),
        $rpm,
        $height
    );
}
add_shortcode( 'planetary_gear_explorer', 'pgx_shortcode' );

/**
 * Add type="module" so the Vite ES module bundle loads correctly.
 *
 * @param string $tag    Script tag HTML.
 * @param string $handle Script handle.
 * @return string Modified script tag.
 */
function pgx_script_type( $tag, $handle ) {
    if ( 'planetary-gear-explorer' !== $handle ) {
        return $tag;
    }
    return str_replace( '<script ', '<script type="module" ', $tag );
}
add_filter( 'script_loader_tag', 'pgx_script_type', 10, 2 );
