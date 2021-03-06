# -*- coding: utf-8; -*-
#
# This file is part of Superdesk.
#
# Copyright 2013, 2014 Sourcefabric z.u. and contributors.
#
# For the full copyright and license information, please see the
# AUTHORS and LICENSE files distributed with this source code, or
# at https://www.sourcefabric.org/superdesk/license

import json
from superdesk.publish.formatters import Formatter
import superdesk
from superdesk.errors import FormatterError
from superdesk.metadata.item import ITEM_TYPE, CONTENT_TYPE, EMBARGO
from superdesk.metadata.packages import RESIDREF, GROUP_ID, GROUPS, ROOT_GROUP, REFS
from superdesk.utils import json_serialize_datetime_objectId


class NINJSFormatter(Formatter):
    """
    NINJS Formatter
    """
    direct_copy_properties = ['versioncreated', 'usageterms', 'subject', 'language', 'headline',
                              'urgency', 'pubstatus', 'mimetype', 'renditions', 'place',
                              'body_text', 'body_html']

    def format(self, article, subscriber):
        try:
            pub_seq_num = superdesk.get_resource_service('subscribers').generate_sequence_number(subscriber)

            ninjs = {
                '_id': article['_id'],
                'version': str(article['_current_version']),
                'type': self._get_type(article)
            }
            try:
                ninjs['byline'] = self._get_byline(article)
            except:
                pass

            located = article.get('dateline', {}).get('located', {})
            if located:
                ninjs['located'] = located.get('city', '')

            for copy_property in self.direct_copy_properties:
                if copy_property in article:
                    ninjs[copy_property] = article[copy_property]

            if 'description' in article:
                ninjs['description_text'] = article['description']

            if article[ITEM_TYPE] == CONTENT_TYPE.COMPOSITE:
                ninjs['associations'] = self._get_associations(article)

            if article.get(EMBARGO):
                ninjs['embargoed'] = article.get(EMBARGO).isoformat()

            ninjs['priority'] = article.get('priority', 5)

            return [(pub_seq_num, json.dumps(ninjs, default=json_serialize_datetime_objectId))]
        except Exception as ex:
            raise FormatterError.ninjsFormatterError(ex, subscriber)

    def can_format(self, format_type, article):
        return format_type == 'ninjs'

    def _get_byline(self, article):
        if 'byline' in article:
            return article['byline'] or ''
        user = superdesk.get_resource_service('users').find_one(req=None, _id=article['original_creator'])
        if user:
            return user['display_name'] or ''
        raise Exception('User not found')

    def _get_type(self, article):
        if article[ITEM_TYPE] == CONTENT_TYPE.PREFORMATTED:
            return CONTENT_TYPE.TEXT
        return article[ITEM_TYPE]

    def _get_associations(self, article):
        associations = dict()
        for group in article[GROUPS]:
            if group[GROUP_ID] == ROOT_GROUP:
                continue

            for ref in group[REFS]:
                if RESIDREF in ref:
                    items = associations.get(group[GROUP_ID], [])
                    item = {}
                    item['_id'] = ref[RESIDREF]
                    item[ITEM_TYPE] = ref[ITEM_TYPE]
                    items.append(item)
                    associations[group[GROUP_ID]] = items
        return associations
