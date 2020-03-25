from odoo import fields, models, api, exceptions


class Checkout(models.Model):
    _name = 'library.checkout'
    _description = 'Checkout Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    _rec_name = 'member_id'

    def button_done(self):
        stages = self.env['library.checkout.stage']
        done_stage = stages.search([('state', '=', 'done')], limit=1)
        for checkout in self:
            checkout.stage_id = done_stage
        return True

    member_id = fields.Many2one(
        'library.member',
        'Library Member',
        required=True
    )

    member_image = fields.Binary(related='member_id.partner_id.image')

    user_id = fields.Many2one(
        'res.users',
        'Librarian',
        default=lambda s: s.env.uid
    )

    request_date = fields.Date(
        default=lambda s: fields.Date.today())

    checkout_date = fields.Date(readonly=True)
    closed_date = fields.Date(readonly=True)

    @api.model
    def create(self, vals):
        # Code before create: should use the `vals` dict
        if 'stage_id' in vals:
            Stage = self.env['library.checkout.stage']
            new_state = Stage.browse(vals['stage_id']).state
            if new_state == 'open':
                vals['checkout_date'] = fields.Date.today()

        new_record = super().create(vals)

        # Code after create: can use the `new_record` created
        if new_record.state == 'done':
            raise exceptions.UserError(
                'Not allowed to create a checkout in the done state.')

        return new_record

    line_ids = fields.One2many(
        'library.checkout.line',
        'checkout_id',
        string='Borrowed Books'
    )

    @api.model
    def _default_stage(self):
        stage = self.env['library.checkout.stage'].search([], limit=1)
        return stage

    @api.model
    def _group_expand_stage_id(self, stages, domain, order):
        return stages.search([], order=order)

    stage_id = fields.Many2one(
        'library.checkout.stage',
        default=_default_stage,
        group_expand='_group_expand_stage_id')

    state = fields.Selection(related='stage_id.state')

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

    # Smart Button
    num_other_checkouts = fields.Integer(compute='_compute_num_other_checkouts')

    def _compute_num_other_checkouts(self):
        for rec in self:
            domain = [
                ('member_id', '=', rec.member_id.id),
                ('state', 'in', ['open']),
                ('id', '!=', rec.id)
            ]
            rec.num_other_checkouts = self.search_count(domain)


class CheckoutLine(models.Model):
    _name = 'library.checkout.line'
    _description = 'Borrow Request Line'

    checkout_id = fields.Many2one('library.checkout')
    book_id = fields.Many2one('library.book')
