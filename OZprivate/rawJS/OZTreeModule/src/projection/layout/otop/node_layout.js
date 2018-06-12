import NodeLayoutBase from '../node_layout_helper';
import config from '../../../global_config';

import tree_state from '../../../tree_state';
import {color_theme} from '../../../themes/color_theme';
import ArcShape from '../../shapes/arc_shape';
import TextShape from '../../shapes/text_shape';
import ImageShape from '../../shapes/image_shape';
import ArcTextShape from '../../shapes/arc_text_shape';
import {ageAsText, gpmapper, is_primary_or_secondary_name} from '../../../factory/utils';
import {add_mr} from '../../move_restriction';
import {global_button_action} from '../../../button_manager';
import {live_area_config} from '../../live_area_config';

class NodeLayout extends NodeLayoutBase
{
    /** Don't include any circles */
    interior_circle_shapes(node, shapes) {
    }

    /** Only render low-res text */
    high_res_shapes(node, shapes) {
        this.low_res_shapes(node, shapes);
    }

    /** Low-res text, but clickable unlike normal */
    low_res_shapes(node, shapes) {
        if ((node.cname || node.latin_name) && !this.hovered && this.is_mouse_over_high_res_text(node)) {
          this.hovered = true;
          this.hovering = true;
          live_area_config.interior_high_res_text.register_button_event(node);
        }
        this.low_res_text_shapes(node, shapes);
        this.hovering = false;
    }
}

export default NodeLayout;
