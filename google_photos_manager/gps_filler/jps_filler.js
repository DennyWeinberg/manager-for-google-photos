// *** Helper functions ***
_next_photo = function() {
    document.querySelectorAll('div[aria-label="View next photo"]').forEach((element) => {
        element.click();
    })
}

// *** Main function ***
do_it = function(loop_mode, force) {
    photo_index = window.location.href.lastIndexOf('/photo/')
    if (photo_index < 0) {
        console.log('Error: Please click on a photo in google photos')
    } else {
        photo_id = window.location.href.substring(photo_index + 7)
        parent_container_list = document.querySelectorAll('c-wiz[jslog*="' + photo_id + '"]')
        if (parent_container_list.length == 0) {
            console.log('Warning: No container found --> Trying again...');

            // Try again
        } else if (parent_container_list.length > 1) {
            alert('Error: Multiple parent container found')
        } else {
            parent_container = parent_container_list[0];

            description_element_list = parent_container.getElementsByTagName("textarea");
            if (description_element_list.length == 0) {
                alert('Error: No textareas found');
            } else if (description_element_list.length > 1) {
                alert('Error: Multiple textareas found');
            } else {
                description_element = description_element_list[0];

                already_done = description_element.value.indexOf('GPS:')
                if (already_done >= 0 && !force) {
                    console.log('Already done');

                    // Go to the next photo
                    return true;
                } else {
                    map_element = parent_container.querySelector('a[href*="/maps?q="]');
                    if (map_element) {
                        res = map_element.href.match(/[-]?\d+(\.\d+),[-]?\d+(\.\d+)/g);
                        if (!res) {
                            console.log('No position found');

                            // Go to the next photo
                            return true;
                        } else {
                            new_string = 'GPS:' + res[0] + ";"

                            if (already_done >= 0) {
                                description_element.value = description_element.value.replace(/GPS:.*;/, new_string)
                            } else {
                                new_value_separator = description_element.value.length > 0 ? ' - ' : ''
                                description_element.value += (new_value_separator + new_string);
                            }

                            // Fire save event
                            description_element.dispatchEvent(new Event('change', {
                                bubbles: true
                            }));
                            console.log('Done');

                            // Go to the next photo
                            return true;
                        }
                    } else {
                        console.log('No map found');

                        // Go to the next photo
                        return true;
                    }
                }
            }
        }
    }

    return false;
}

// === One time force mode ===
// do_it(false, true);

// === Loop mode ===
_do_loop = function() {
    setTimeout(function() {
        // loop, force
        done = do_it(true, false);

        setTimeout(function() {
            if (done) {
                _next_photo();
            }

            _do_loop();
        }, 800);
    }, 200);
}
_do_loop();
