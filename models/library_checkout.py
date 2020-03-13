from odoo import fields, models, api


class Checkout(models.Model):
    _name = 'library.checkout'
    _description = 'Checkout Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.multi
    def action_open(self):
        self.ensure_one()
        for rec in self:
            rec.state = 'open'

    @api.multi
    def action_done(self):
        self.ensure_one()
        for rec in self:
            rec.state = 'done'

    member_id = fields.Many2one(
        'library.member',
        'Library Member',
        required=True
    )

    user_id = fields.Many2one(
        'res.users',
        'Librarian',
        default=lambda s: s.env.uid
    )

    request_date = fields.Date(
        default=lambda s: fields.Date.today())

    line_ids = fields.One2many(
        'library.checkout.line',
        'checkout_id',
        string='Borrowed Books'
    )

    # to add in the class Checkout:
    @api.model
    def _default_stage(self):
        Stage = self.env['library.checkout.stage'].search([], limit=1)
        return Stage

    @api.model
    def _group_expand_stage_id(self, stages, domain, order):
        return stages.search([], order=order)

    stage_id = fields.Many2one(
     'library.checkout.stage',
     default=_default_stage,
     group_expand='_group_expand_stage_id')

    state = fields.Selection(related='stage_id.state', store=True)

    @api.onchange('member_id')
    def onchange_member_id(self):
        today = fields.Date.today()
        if self.request_date != today:
            self.request_date = fields.Date.today()
            return {
                'warning': {
                    'title': 'Changed Request Date',
                    'message': 'Request date changed to today.',
                }
            }


class CheckoutLine(models.Model):
    _name = 'library.checkout.line'
    _description = 'Borrow Request Line'
    _rec_name = 'book_id'

    checkout_id = fields.Many2one('library.checkout')
    book_id = fields.Many2one('library.book')
