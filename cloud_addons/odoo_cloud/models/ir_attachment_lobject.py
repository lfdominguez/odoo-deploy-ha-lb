
# Based on https://github.com/it-projects-llc/misc-addons/tree/12.0/attachment_large_object
# with tweaks to add dblo: to the start of the store_fname field

import logging
import base64
from odoo import models, api, SUPERUSER_ID, _
from odoo.addons.base.models.ir_attachment import IrAttachment
from odoo.exceptions import AccessError
import psycopg2

LARGE_OBJECT_LOCATION = 'dblo'
log = logging.getLogger(__name__)


def monkey_patch_ir_attachment():
    """Provide storage as PostgreSQL large objects of attachements with filestore location ``dblo``.

    Works by overriding the storage handling methods of ``ir.attachment``, as intended by the
    default implementation. We have to monkey patch because we want the base attachments to
    be stored in large objects too :)
    """

    @api.model
    def _lobject(self, cr, *args):
        return cr._cnx.lobject(*args)
    setattr(IrAttachment, '_lobject', _lobject)

    def _is_dblo_attachment(self, fname):
        return fname and fname.startswith(LARGE_OBJECT_LOCATION + ':')
    setattr(IrAttachment, '_is_dblo_attachment', _is_dblo_attachment)

    @api.model
    def _file_write(self, value, checksum):
        """Write the content in a newly created large object.

        :param value: base64 encoded payload
        :returns str: object id (will be considered the file storage name)
        """
        location = self._storage()
        if location != LARGE_OBJECT_LOCATION:
            return self._orig_file_write(value, checksum)

        lobj = self._lobject(self.env.cr, 0, 'wb')  # oid=0 means creation
        lobj.write(base64.b64decode(value))
        oid = lobj.oid
        return LARGE_OBJECT_LOCATION + ':' + str(oid)
    setattr(IrAttachment, '_orig_file_write', IrAttachment._file_write)
    setattr(IrAttachment, '_file_write', _file_write)

    def _file_delete(self, fname):
        if self._is_dblo_attachment(fname):
            oid = int(fname[len(LARGE_OBJECT_LOCATION)+1:])
            self.env.cr.execute("SAVEPOINT lobject_delete")
            try:
                return self._lobject(self.env.cr, oid, 'rb').unlink()
            except psycopg2.OperationalError:
                self.env.cr.execute("ROLLBACK TO SAVEPOINT lobject_delete")
        else:
            return self._orig_file_delete(fname)
    setattr(IrAttachment, '_orig_file_delete', IrAttachment._file_delete)
    setattr(IrAttachment, '_file_delete', _file_delete)

    def _lobject_read(self, fname, bin_size):
        """Read the large object, base64 encoded.

        :param fname: file storage name, must be the oid as a string.
        """
        oid = int(fname[len(LARGE_OBJECT_LOCATION)+1:])
        lobj = self._lobject(self.env.cr, oid, 'rb')
        if bin_size:
            return lobj.seek(0, 2)
        # GR TODO it must be possible to read-encode in chunks
        return base64.b64encode(lobj.read())
    setattr(IrAttachment, '_lobject_read', _lobject_read)

    @api.depends('store_fname', 'db_datas')
    def _compute_datas(self):
        for attach in self:
            if self._is_dblo_attachment(attach.store_fname):
                bin_size = self._context.get('bin_size')
                attach.datas = self._lobject_read(attach.store_fname, bin_size)
            else:
                attach._orig_compute_datas()
    setattr(IrAttachment, '_orig_compute_datas', IrAttachment._compute_datas)
    setattr(IrAttachment, '_compute_datas', _compute_datas)

    @api.model
    def _storage(self):
        return self.env['ir.config_parameter'].sudo().get_param('ir_attachment.location', LARGE_OBJECT_LOCATION)
    setattr(IrAttachment, '_storage', _storage)

    @api.model
    def migrate_to_lobject(self):
        """migrates all binary attachments to postgres large object storage"""
        if not self.env.user._is_admin():
            raise AccessError(
                _('Only administrators can execute this action.'))

        atts = self.search([
            '&', '&',
            ('id', '>', 0),  # bypass filtering of field-attached attachments
            ('type', '=', 'binary'),
            '|',
            ('store_fname', '=', False), ('store_fname',
                                          'not like', LARGE_OBJECT_LOCATION + ':%')
        ])

        att_count = len(atts)
        if att_count:
            log.info(
                f'Migrating {att_count} database attachments to Large Objects...')
            if self._storage() != LARGE_OBJECT_LOCATION:
                raise Exception(
                    f'Default storage is not set to Large Object ({LARGE_OBJECT_LOCATION})')
            current_att = 1
            for att in atts:
                log.info(
                    f'Migrating attachment ID {att.id} ({current_att} of {att_count})...')
                # re-save data to move to lobject storage
                att.write({
                    'mimetype': att.mimetype,
                    'datas': att.datas
                })
                current_att += 1
    setattr(IrAttachment, 'migrate_to_lobject', migrate_to_lobject)
